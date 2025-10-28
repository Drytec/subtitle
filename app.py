from flask import Flask, request, jsonify
import requests, os, tempfile, time

app = Flask(__name__)
ASSEMBLYAI_API_KEY = os.getenv("ASSEMBLYAI_API_KEY")
HEADERS = {"authorization": ASSEMBLYAI_API_KEY}

@app.route("/generate_subtitles", methods=["POST"])
def generate_subtitles():
    try:
        data = request.get_json()
        video_url = data.get("url")
        if not video_url:
            return jsonify({"error": "Falta el campo 'url'"}), 400

        # 🔹 Paso 1: Descargar el video temporalmente
        headers = {"User-Agent": "Mozilla/5.0"}
        with requests.get(video_url, headers=headers, stream=True, timeout=60) as r:
            r.raise_for_status()
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp:
                for chunk in r.iter_content(chunk_size=8192):
                    tmp.write(chunk)
                tmp_path = tmp.name

        # 🔹 Paso 2: Subir a AssemblyAI
        with open(tmp_path, "rb") as f:
            upload_res = requests.post("https://api.assemblyai.com/v2/upload", headers=HEADERS, data=f)
        upload_res.raise_for_status()
        audio_url = upload_res.json()["upload_url"]

        # 🔹 Paso 3: Crear transcripción
        transcript_res = requests.post(
            "https://api.assemblyai.com/v2/transcript",
            json={"audio_url": audio_url, "speaker_labels": False, "language_detection": True},
            headers=HEADERS
        )
        transcript_res.raise_for_status()
        transcript_id = transcript_res.json()["id"]

        return jsonify({
            "message": "Transcripción iniciada",
            "transcript_id": transcript_id
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/get_subtitles/<transcript_id>")
def get_subtitles(transcript_id):
    try:
        while True:
            polling = requests.get(f"https://api.assemblyai.com/v2/transcript/{transcript_id}", headers=HEADERS)
            data = polling.json()
            if data["status"] == "completed":
                return jsonify({
                    "text": data["text"],
                    "subtitles": data.get("words", [])
                })
            elif data["status"] == "error":
                return jsonify({"error": data["error"]}), 500
            time.sleep(5)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
