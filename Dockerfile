FROM python:3.8-slim

RUN apt-get update && apt-get install -y \
    git ffmpeg build-essential libgl1 libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app/backend

# 1. Clone SadTalker
RUN git clone https://github.com/Winfredy/SadTalker.git SadTalker

# 2. Install SadTalker's own requirements (CPU-only torch, since Render has no GPU)
WORKDIR /app/backend/SadTalker
RUN pip install --upgrade pip setuptools wheel
RUN pip install torch==1.12.1+cpu torchvision==0.13.1+cpu torchaudio==0.12.1 \
    --extra-index-url https://download.pytorch.org/whl/cpu
RUN pip install -r requirements.txt
RUN bash scripts/download_models.sh

# 3. Install API dependencies
WORKDIR /app/backend
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY app.py .

EXPOSE 8000
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
