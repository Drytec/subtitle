from flask import Flask, request, jsonify
import requests, tempfile, os
from moviepy.editor import VideoFileClip

app = Flask(__name__)

# Modelo gratuito en Hugging Face
HF_API_URL = "https://api-inference.huggingface.co/models/Salesforce/blip-image-captioning-base"


def generate_descriptive_subtitles(video_url):
    try:
        # Paso 1️⃣ — Descargar el video temporalmente
        headers = {"User-Agent": "Mozilla/5.0"}
        with requests.get(video_url, headers=headers, stream=True, timeout=60) as r:
            r.raise_for_status()
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp:
                for chunk in r.iter_content(chunk_size=8192):
                    tmp.write(chunk)
                tmp_path = tmp.name

        # Paso 2️⃣ — Capturar un fotograma (segundo 2)
        clip = VideoFileClip(tmp_path)
        frame = clip.get_frame(2.0)
        clip.close()

        # Paso 3️⃣ — Convertir el fotograma a bytes JPG
        import io
        from PIL import Image
        img_bytes = io.BytesIO()
        Image.fromarray(frame).save(img_bytes, format="JPEG")
        img_bytes.seek(0)

        # Paso 4️⃣ — Enviar imagen al modelo de Hugging Face
        response = requests.post(
            HF_API_URL,
            headers={"Content-Type": "application/octet-stream"},
            data=img_bytes.read(),
            timeout=60
        )

        result = response.json()

        # Paso 5️⃣ — Devolver la descripción
        if isinstance(result, list) and "generated_text" in result[0]:
            return {"description": result[0]["generated_text"]}
        else:
            return {"error": "No se pudo generar la descripción", "details": result}

    except Exception as e:
        return {"error": str(e)}


@app.route("/describe_video", methods=["POST"])
def describe_video_endpoint():
    data = request.get_json()
    video_url = data.get("url")

    if not video_url:
        return jsonify({"error": "Falta el campo 'url'"}), 400

    result = generate_descriptive_subtitles(video_url)
    return jsonify(result)


@app.route("/")
def home():
    return jsonify({
        "message": "API activa. Usa POST /describe_video con {'url': 'URL_DEL_VIDEO'} para generar subtítulos descriptivos."
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 10000)))
