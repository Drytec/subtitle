from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

ASSEMBLYAI_API_KEY = os.getenv("ASSEMBLYAI_API_KEY")

@app.route("/subtitles_from_url", methods=["POST"])
def subtitles_from_url():
    try:
        video_url = request.form["url"]

        # Paso 1️⃣ — Enviar el video a AssemblyAI para transcripción
        headers = {"authorization": ASSEMBLYAI_API_KEY}
        data = {"audio_url": video_url}

        response = requests.post("https://api.assemblyai.com/v2/transcript", json=data, headers=headers)
        transcript_id = response.json()["id"]

        # Paso 2️⃣ — Esperar a que termine la transcripción
        while True:
            polling_response = requests.get(
                f"https://api.assemblyai.com/v2/transcript/{transcript_id}",
                headers=headers
            )
            status = polling_response.json()["status"]

            if status == "completed":
                text = polling_response.json()["text"]
                return jsonify({"text": text})
            elif status == "error":
                return jsonify({"error": polling_response.json()["error"]}), 500

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
