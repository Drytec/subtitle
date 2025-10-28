from transformers import pipeline
from flask import Flask, request, jsonify
import torch

app = Flask(__name__)

# 🧠 Cargar modelo solo una vez
device = 0 if torch.cuda.is_available() else -1
whisper = pipeline("automatic-speech-recognition", model="openai/whisper-tiny", device=device)

@app.route("/subtitles_from_url", methods=["POST"])
def generate_subtitles():
    try:
        video_url = request.form["url"]

        # Descargar solo el audio
        import subprocess
        subprocess.run(["ffmpeg", "-y", "-i", video_url, "-vn", "-acodec", "mp3", "audio.mp3"], check=True)

        result = whisper("audio.mp3")  # Transcripción
        return jsonify({"text": result["text"]})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
