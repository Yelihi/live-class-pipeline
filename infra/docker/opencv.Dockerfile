FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    wget \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY apps/opencv-pipeline/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

RUN mkdir -p /app/media/models && \
    wget -q --timeout=60 \
    -O /app/media/models/face_landmarker.task \
    "https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task"

COPY apps/opencv-pipeline/src/ /app/src/
RUN mkdir -p /tmp/hls /app/output

CMD ["python3", "-m", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
