from flask import Flask, request, jsonify
import requests, tempfile, os, cv2
from transformers import pipeline

app = Flask(__name__)

captioner = pipeline("image-to-text", model="Salesforce/blip-image-captioning-base")

@app.route("/describe", methods=["POST"])
def describe_video():
    data = request.json
    video_url = data.get("video_url")

    if not video_url:
        return jsonify({"error": "Missing video_url"}), 400

    try:
        response = requests.get(video_url)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp:
            tmp.write(response.content)
            tmp_path = tmp.name

        cap = cv2.VideoCapture(tmp_path)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        if frame_count == 0:
            return jsonify({"error": "El video no tiene fotogramas válidos"}), 400

        interval = max(1, frame_count // 5)
        frames = []
        for i in range(0, frame_count, interval):
            cap.set(cv2.CAP_PROP_POS_FRAMES, i)
            ret, frame = cap.read()
            if ret:
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                frames.append(frame)
        cap.release()

        if not frames:
            return jsonify({"error": "No se pudieron extraer imágenes del video"}), 400

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
