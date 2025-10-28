from flask import Flask, request, jsonify
import requests
import os
import tempfile

app = Flask(__name__)

ASSEMBLYAI_API_KEY = os.getenv("ASSEMBLYAI_API_KEY")
HEADERS = {"authorization": ASSEMBLYAI_API_KEY}

@app.route("/subtitles_from_url", methods=["POST"])
def subtitles_from_url():
    try:
        video_url = request.form["url"]

        # Paso 1️⃣ — Descargar el video temporalmente
        headers = {"User-Agent": "Mozilla/5.0"}
        with requests.get(video_url, headers=headers, stream=True, timeout=60) as r:
            r.raise_for_status()
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp:
                for chunk in r.iter_content(chunk_size=8192):
                    tmp.write(chunk)
                tmp_path = tmp.name

        # Paso 2️⃣ — Subir el video a AssemblyAI
        with open(tmp_path, "rb") as f:
            upload_response = requests.post(
                "https://api.assemblyai.com/v2/upload",
                headers=HEADERS,
                data=f
            )
        audio_url = upload_response.json()["upload_url"]

        # Paso 3️⃣ — Solicitar transcripción
        transcript_response = requests.post(
            "https://api.assemblyai.com/v2/transcript",
            json={"audio_url": audio_url},
            headers=HEADERS
        )
        transcript_id = transcript_response.json()["id"]

        # Paso 4️⃣ — Esperar a que termine
        while True:
            polling_response = requests.get(
                f"https://api.assemblyai.com/v2/transcript/{transcript_id}",
                headers=HEADERS
            )
            status = polling_response.json()["status"]

            if status == "completed":
                return jsonify({"text": polling_response.json()["text"]})
            elif status == "error":
                return jsonify({"error": polling_response.json()["error"]}), 500

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
