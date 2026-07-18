import os
import shutil
import subprocess
import uuid
from pathlib import Path

from fastapi import FastAPI, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, HTMLResponse
from gtts import gTTS

app = FastAPI(title="Talking Face Generator API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

FRONTEND_HTML = """
<!DOCTYPE html>
<html lang="en">

<head>
  <meta charset="UTF-8">
  <title>BolChehra — Talking Face Generator</title>
  <style>
    body {
      font-family: -apple-system, Segoe UI, Roboto, sans-serif;
      max-width: 560px;
      margin: 60px auto;
      padding: 0 20px;
      color: #1a1a1a;
    }

    .brand {
      display: flex;
      align-items: center;
      gap: 12px;
      margin-bottom: 4px;
    }

    .brand svg {
      width: 44px;
      height: 44px;
      flex-shrink: 0;
    }

    .brand h1 {
      font-size: 26px;
      margin: 0;
      letter-spacing: -0.5px;
    }

    p.sub {
      color: #666;
      margin-top: 4px;
      margin-bottom: 0;
    }

    label {
      display: block;
      font-weight: 600;
      margin-top: 20px;
      margin-bottom: 6px;
    }

    input[type="file"],
    textarea {
      width: 100%;
      padding: 10px;
      border: 1px solid #ccc;
      border-radius: 8px;
      font-size: 14px;
      box-sizing: border-box;
    }

    textarea {
      min-height: 90px;
      resize: vertical;
    }

    button {
      margin-top: 24px;
      width: 100%;
      padding: 12px;
      background: #d97757;
      color: white;
      border: none;
      border-radius: 8px;
      font-size: 15px;
      font-weight: 600;
      cursor: pointer;
    }

    button:disabled {
      background: #ccc;
      cursor: not-allowed;
    }

    #status {
      margin-top: 16px;
      font-size: 14px;
      color: #555;
    }

    video {
      margin-top: 20px;
      width: 100%;
      border-radius: 8px;
    }

    .limit-notice {
      margin-top: 8px;
      padding: 10px 12px;
      background: #fff4e5;
      border: 1px solid #f0b955;
      border-left: 4px solid #d97757;
      border-radius: 6px;
      font-size: 13px;
      color: #7a4a1a;
      line-height: 1.5;
    }

    .char-counter {
      margin-top: 6px;
      font-size: 12px;
      color: #888;
      text-align: right;
    }

    .char-counter.over {
      color: #c0392b;
      font-weight: 600;
    }
  </style>
</head>

<body>
  <div class="brand">
    <svg viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
      <circle cx="50" cy="50" r="48" fill="#d97757" />
      <circle cx="50" cy="46" r="22" fill="#fff" />
      <circle cx="42" cy="42" r="3.2" fill="#d97757" />
      <circle cx="58" cy="42" r="3.2" fill="#d97757" />
      <path d="M40 54 Q50 62 60 54" stroke="#d97757" stroke-width="3" fill="none" stroke-linecap="round" />
      <path d="M14 38 Q8 50 14 62" stroke="#fff" stroke-width="4" fill="none" stroke-linecap="round" />
      <path d="M22 32 Q13 50 22 68" stroke="#fff" stroke-width="4" fill="none" stroke-linecap="round" opacity="0.6" />
      <path d="M86 38 Q92 50 86 62" stroke="#fff" stroke-width="4" fill="none" stroke-linecap="round" />
      <path d="M78 32 Q87 50 78 68" stroke="#fff" stroke-width="4" fill="none" stroke-linecap="round" opacity="0.6" />
    </svg>
    <h1>BolChehra</h1>
  </div>
  <p class="sub">Upload a photo, type a script, get a talking video.</p>

  <form id="genForm">
    <label for="image">Photo (face image)</label>
    <input type="file" id="image" accept="image/*" required>

    <label for="script">Script</label>
    <textarea id="script" placeholder="Apna script yahan likho..." required></textarea>
    <div class="char-counter" id="charCounter">0 / 5000 characters</div>
    <div class="limit-notice">
      ⚠️ <strong>Script 5000 characters se zyada na ho.</strong> Isse zyada lamba text (jaise 2000-3000 words wala poora
      script) ek saath process nahi ho payega — audio/video generation fail ho sakta hai. Lambe script ko chhote hisso
      mein todke alag-alag videos banao.
    </div>

    <button type="submit" id="submitBtn">Generate Video</button>
  </form>

  <div id="status"></div>
  <video id="resultVideo" controls style="display:none;"></video>

  <script>
    // Empty = same origin (this page and the API are served from the same server)
    const API_URL = "";

    const form = document.getElementById("genForm");
    const statusEl = document.getElementById("status");
    const btn = document.getElementById("submitBtn");
    const videoEl = document.getElementById("resultVideo");
    const scriptEl = document.getElementById("script");
    const charCounterEl = document.getElementById("charCounter");
    const MAX_CHARS = 5000;

    scriptEl.addEventListener("input", () => {
      const len = scriptEl.value.length;
      charCounterEl.textContent = `${len} / ${MAX_CHARS} characters`;
      charCounterEl.classList.toggle("over", len > MAX_CHARS);
    });

    form.addEventListener("submit", async (e) => {
      e.preventDefault();

      const imageFile = document.getElementById("image").files[0];
      const script = document.getElementById("script").value;

      if (!imageFile || !script) return;

      if (script.length > MAX_CHARS) {
        statusEl.textContent = `Script bahut lamba hai (${script.length} characters). Kripya ${MAX_CHARS} characters se kam karo.`;
        return;
      }

      const formData = new FormData();
      formData.append("image", imageFile);
      formData.append("script", script);

      btn.disabled = true;
      btn.textContent = "Generating... (this can take a few minutes)";
      statusEl.textContent = "Processing your video, please wait...";
      videoEl.style.display = "none";

      try {
        const res = await fetch(`${API_URL}/generate`, {
          method: "POST",
          body: formData,
        });

        if (!res.ok) {
          const err = await res.json().catch(() => ({}));
          throw new Error(err.error || "Something went wrong");
        }

        const blob = await res.blob();
        const videoUrl = URL.createObjectURL(blob);
        videoEl.src = videoUrl;
        videoEl.style.display = "block";
        statusEl.textContent = "Done!";
      } catch (err) {
        statusEl.textContent = "Error: " + err.message;
      } finally {
        btn.disabled = false;
        btn.textContent = "Generate Video";
      }
    });
  </script>
</body>

</html>
"""


@app.get("/", response_class=HTMLResponse)
def serve_frontend():
    return FRONTEND_HTML


BASE_DIR = Path(__file__).resolve().parent
SADTALKER_DIR = BASE_DIR / "SadTalker"
UPLOAD_DIR = BASE_DIR / "uploads"
RESULT_DIR = BASE_DIR / "results"

UPLOAD_DIR.mkdir(exist_ok=True)
RESULT_DIR.mkdir(exist_ok=True)

MAX_SCRIPT_CHARS = 5000


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/generate")
async def generate(image: UploadFile = File(...), script: str = Form(...)):
    if len(script) > MAX_SCRIPT_CHARS:
        return JSONResponse(
            status_code=400,
            content={"error": f"Script too long ({len(script)} chars). Max allowed is {MAX_SCRIPT_CHARS} characters."},
        )

    job_id = str(uuid.uuid4())[:8]

    image_path = UPLOAD_DIR / f"{job_id}_{image.filename}"
    with open(image_path, "wb") as f:
        shutil.copyfileobj(image.file, f)

    audio_path = UPLOAD_DIR / f"{job_id}.mp3"
    tts = gTTS(text=script, lang="en", tld="co.in", slow=False)
    tts.save(str(audio_path))

    job_result_dir = RESULT_DIR / job_id
    job_result_dir.mkdir(exist_ok=True)

    cmd = [
        "python3.8", "inference.py",
        "--driven_audio", str(audio_path.resolve()),
        "--source_image", str(image_path.resolve()),
        "--result_dir", str(job_result_dir.resolve()),
        "--preprocess", "full",
        "--enhancer", "gfpgan",
        "--size", "512",
        "--batch_size", "32",
    ]

    try:
        subprocess.run(cmd, cwd=str(SADTALKER_DIR), check=True, timeout=1800)
    except subprocess.CalledProcessError as e:
        return JSONResponse(status_code=500, content={"error": "Inference failed", "detail": str(e)})
    except subprocess.TimeoutExpired:
        return JSONResponse(status_code=504, content={"error": "Inference timed out (video generation takes too long on this server)"})

    mp4_files = list(job_result_dir.glob("**/*.mp4"))
    if not mp4_files:
        return JSONResponse(status_code=500, content={"error": "No output video found"})

    return FileResponse(mp4_files[0], media_type="video/mp4", filename=f"{job_id}.mp4")