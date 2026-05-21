#!/usr/bin/env bash
# GStreamer 1.0 설치 스크립트 (Ubuntu 22.04 전용)
# Dev Container 또는 Ubuntu VM에서 실행한다.
# Mac 로컬에서는 apt-get 미지원 → .devcontainer 사용 권장
set -euo pipefail
export DEBIAN_FRONTEND=noninteractive

echo "==> [1/3] 패키지 목록 업데이트"
apt-get update -qq
apt-get install -y --no-install-recommends software-properties-common
add-apt-repository universe -y
apt-get update -qq

echo "==> [2/3] GStreamer 및 Python 바인딩 설치"
apt-get install -y --no-install-recommends \
  gstreamer1.0-tools \
  gstreamer1.0-plugins-base \
  gstreamer1.0-plugins-good \
  gstreamer1.0-plugins-bad \
  gstreamer1.0-plugins-ugly \
  gstreamer1.0-libav \
  python3-gst-1.0 \
  python3-gi \
  gir1.2-gstreamer-1.0 \
  gir1.2-gst-plugins-base-1.0 \
  python3-pip \
  python3-venv \
  libgl1 \
  libglib2.0-0

echo ""
echo "==> [3/3] 설치 확인"
gst-launch-1.0 --version

echo ""
echo "==> 동작 확인: videotestsrc 30프레임 생성 후 종료"
gst-launch-1.0 videotestsrc num-buffers=30 ! fakesink

echo ""
echo "==> T-01 완료: GStreamer 설치 성공"
