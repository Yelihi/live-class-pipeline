FROM ubuntu:22.04
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

# 1. 시스템 패키지 — 자주 변하지 않으므로 가장 먼저 설치
RUN apt-get update && \
    apt-get install -y software-properties-common && \
    add-apt-repository universe && \
    apt-get update && \
    apt-get install -y \
      # GStreamer 핵심
      gstreamer1.0-tools \
      gstreamer1.0-plugins-base \
      gstreamer1.0-plugins-good \
      gstreamer1.0-plugins-bad \
      gstreamer1.0-plugins-ugly \
      gstreamer1.0-libav \
      # x264 인코더
      gstreamer1.0-x \
      # Python GI 바인딩 (pip 설치 불가 — apt 필수)
      python3-gst-1.0 \
      python3-gi \
      gir1.2-gstreamer-1.0 \
      gir1.2-gst-plugins-base-1.0 \
      # Python 기본
      python3-pip \
      python3-dev \
      # MediaPipe / OpenCV 의존성
      libgl1 \
      libglib2.0-0 \
      libsm6 \
      libxext6 \
      libxrender-dev \
      # 유틸리티
      wget \
      curl && \
    rm -rf /var/lib/apt/lists/*

# 2. Python 패키지 — requirements.txt 변경 시만 재실행
WORKDIR /app
COPY apps/control-api/requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# 3. MediaPipe 모델 다운로드
RUN mkdir -p /app/media/models && \
    wget -q -O /app/media/models/face_landmarker.task \
      https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task

# 4. 소스 코드 — 가장 자주 변하므로 마지막에 복사
COPY apps/control-api/src/ /app/src/
COPY media/ /app/media/

# 5. 런타임 디렉토리
RUN mkdir -p /tmp/hls /app/output

EXPOSE 8000

CMD ["python3", "-m", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
