# Talking Face Generator (SadTalker Web App)

Ek simple frontend + backend jo image aur script upload leke talking-face video generate karta hai (SadTalker use karke).

## ⚠️ Important warning before deploying

SadTalker heavy hai — GPU pe fast chalta hai, CPU pe **bahut slow** (kai minutes per video). **Render ke free/basic plans mein GPU nahi milta**, sirf CPU. Isliye:
- Video generation Render pe **1-5+ minute** le sakta hai per request (aur free tier timeout/sleep bhi hoga).
- Docker image bhi bada hoga (SadTalker models ~2-3 GB), jo free tier disk limit se clash kar sakta hai.
- Agar production-quality speed chahiye, GPU-backed host use karo (RunPod, Lambda Labs, AWS EC2 g4dn, ya apna Colab backend hi rakho).

Ye project abhi bhi Render pe deploy ho sakta hai — bas ye expect karo ki CPU pe slow chalega.

## Project structure
```
talking-face-app/
├── backend/
│   ├── app.py            # FastAPI server
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   └── index.html        # Upload form (image + script)
└── README.md
```

## 1. Local test (optional, before deploying)

```bash
cd backend
pip install -r requirements.txt
git clone https://github.com/Winfredy/SadTalker.git
cd SadTalker && pip install -r requirements.txt && bash scripts/download_models.sh
cd ..
uvicorn app:app --reload
```
Then open `frontend/index.html` in a browser (API_URL already points to `http://localhost:8000`).

## 2. Push to GitHub

```bash
cd talking-face-app
git init
git add .
git commit -m "Initial commit: talking face generator app"
git branch -M main
git remote add origin https://github.com/<your-username>/<your-repo>.git
git push -u origin main
```
(Create the empty repo on GitHub first at github.com/new — don't initialize it with a README there, to avoid merge conflicts.)

## 3. Deploy backend on Render

1. Go to [render.com](https://render.com) → **New** → **Web Service**
2. Connect your GitHub repo
3. Settings:
   - **Root Directory:** `backend`
   - **Environment:** Docker (Render will detect the `Dockerfile`)
   - **Instance type:** at least 2GB RAM (free tier may not have enough memory for torch + models)
4. Click **Create Web Service** — first build will take a while (cloning SadTalker + downloading models happens at build time)
5. Once deployed, you'll get a URL like `https://your-app.onrender.com`

## 4. Connect frontend to the deployed backend

In `frontend/index.html`, change:
```js
const API_URL = "http://localhost:8000";
```
to:
```js
const API_URL = "https://your-app.onrender.com";
```

## 5. Host the frontend

Simplest options:
- **GitHub Pages**: push the `frontend` folder to a `gh-pages` branch, or use repo Settings → Pages
- **Render Static Site**: New → Static Site → point Root Directory to `frontend`
- Or just open `index.html` locally / host it anywhere static files are served

## Notes
- The backend generates TTS audio in Indian-accent English (`gTTS` with `tld='co.in'`) from the script text.
- Uploaded images and generated videos are stored temporarily in `backend/uploads/` and `backend/results/` — not committed to git (see `.gitignore`).
