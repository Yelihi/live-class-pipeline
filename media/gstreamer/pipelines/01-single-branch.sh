#!/usr/bin/env bash
# T-02: 단일 브랜치 파이프라인 — 파일 입력 → fakesink
# 사용: bash media/gstreamer/pipelines/01-single-branch.sh [input.mp4]
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SAMPLE_MP4="$SCRIPT_DIR/../sample.mp4"
INPUT="${1:-$SAMPLE_MP4}"

# sample.mp4 가 없으면 videotestsrc 로 자동 생성 (10초, 30fps = 300프레임)
if [[ ! -f "$INPUT" ]]; then
  echo "==> sample.mp4 없음 → videotestsrc로 생성: $INPUT"
  gst-launch-1.0 -q \
    videotestsrc num-buffers=300 ! \
    videoconvert ! \
    x264enc ! \
    mp4mux ! \
    filesink location="$INPUT"
  echo "==> 생성 완료"
fi

echo "==> 입력: $INPUT"
echo "==> 파이프라인 시작 (Ctrl+C 로 종료)"
echo ""

# GUI 환경: 아래 주석을 해제하고 fakesink 줄을 주석 처리
# gst-launch-1.0 -v filesrc location="$INPUT" ! decodebin ! videoconvert ! autovideosink

# 서버/터미널 환경: fakesink 로 동작 확인 (-v 로 caps 협상 정보 출력)
gst-launch-1.0 -v \
  filesrc location="$INPUT" ! \
  decodebin ! \
  videoconvert ! \
  fakesink sync=false || true

echo ""
echo "==> 파이프라인 종료"
