import os
import shutil
import subprocess
import uuid
from pathlib import Path

from fastapi import FastAPI, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from gtts import gTTS

app = FastAPI(title="Talking Face Generator API")

# Allow the frontend (hosted anywhere) to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = Path(__file__).resolve().parent
SADTALKER_DIR = BASE_DIR / "SadTalker"
UPLOAD_DIR = BASE_DIR / "uploads"
RESULT_DIR = BASE_DIR / "results"

UPLOAD_DIR.mkdir(exist_ok=True)
RESULT_DIR.mkdir(exist_ok=True)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/generate")
async def generate(image: UploadFile = File(...), script: str = Form(...)):
    job_id = str(uuid.uuid4())[:8]

    # 1. Save uploaded image
    image_path = UPLOAD_DIR / f"{job_id}_{image.filename}"
    with open(image_path, "wb") as f:
        shutil.copyfileobj(image.file, f)

    # 2. Generate audio from text (Indian-accent English)
    audio_path = UPLOAD_DIR / f"{job_id}.mp3"
    tts = gTTS(text=script, lang="en", tld="co.in", slow=False)
    tts.save(str(audio_path))

    # 3. Run SadTalker inference
    job_result_dir = RESULT_DIR / job_id
    job_result_dir.mkdir(exist_ok=True)

    cmd = [
        "python3.8", "inference.py",
        "--driven_audio", str(audio_path.resolve()),
        "--source_image", str(image_path.resolve()),
        "--result_dir", str(job_result_dir.resolve()),
        "--preprocess", "crop",
        "--still",
        "--batch_size", "10",
        "--size", "256",
    ]

    try:
        subprocess.run(cmd, cwd=str(SADTALKER_DIR), check=True, timeout=1800)
    except subprocess.CalledProcessError as e:
        return JSONResponse(status_code=500, content={"error": "Inference failed", "detail": str(e)})
    except subprocess.TimeoutExpired:
        return JSONResponse(status_code=504, content={"error": "Inference timed out (video generation takes too long on this server)"})

    # 4. Find generated mp4 and return it
    mp4_files = list(job_result_dir.glob("**/*.mp4"))
    if not mp4_files:
        return JSONResponse(status_code=500, content={"error": "No output video found"})

    return FileResponse(mp4_files[0], media_type="video/mp4", filename=f"{job_id}.mp4")
