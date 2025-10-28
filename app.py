from flask import Flask, request, jsonify
import requests, tempfile, os
from moviepy.editor import VideoFileClip
from transformers import pipeline

app = Flask(__name__)

# Modelo de descripción de video (usa visión + lenguaje)
captioner = pipeline("image-to-text", model="Salesforce/blip-image-captioning-base")

@app.route("/describe", methods=["POST"])
def describe_video():
    data = request.json
    video_url = data.get("video_url")

    if not video_url:
        return jsonify({"error": "Missing video_url"}), 400

    try:
        # Descargar el video
        response = requests.get(video_url)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp:
            tmp.write(response.content)
            tmp_path = tmp.name

        # Extraer frames del video
        clip = VideoFileClip(tmp_path)
        duration = clip.duration
        interval = max(1, int(duration // 5))  # 5 descripciones por video
        frames = [clip.get_frame(t) for t in range(0, int(duration), interval)]

        # Generar descripciones
        descriptions = [captioner(frame)[0]["generated_text"] for frame in frames]

        os.remove(tmp_path)
        return jsonify({"subtitles": descriptions})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/")
def home():
    return "Servidor activo. Usa POST /describe para generar subtítulos."

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
