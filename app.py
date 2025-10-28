from fastapi import FastAPI, UploadFile, Form
from transformers import pipeline
import tempfile
import requests

app = FastAPI()

model = pipeline("automatic-speech-recognition", model="openai/whisper-tiny")

@app.post("/subtitles")
async def generate_subtitles(file: UploadFile):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name

    result = model(tmp_path)
    return {"text": result["text"]}


@app.post("/subtitles_from_url")
async def generate_subtitles_from_url(url: str = Form(...)):
    response = requests.get(url, stream=True)
    if response.status_code != 200:
        return {"error": f"No se pudo descargar el video desde {url}"}

    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp:
        for chunk in response.iter_content(chunk_size=8192):
            tmp.write(chunk)
        tmp_path = tmp.name

    result = model(tmp_path)
    return {"text": result["text"]}
