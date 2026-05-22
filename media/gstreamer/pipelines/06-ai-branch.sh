#!/usr/bin/env bash
# T-06: AI branch 저해상도·저FPS 분기 검증
# AI branch: videoscale+videorate → 320×240 5fps → videoconvert → BGR → fakesink
# live branch: 원본 해상도·FPS 유지 → fakesink
# 사용: bash media/gstreamer/pipelines/06-ai-branch.sh [input.mp4]
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SAMPLE_MP4="$SCRIPT_DIR/../sample.mp4"
INPUT="${1:-$SAMPLE_MP4}"

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
echo "==> AI branch: 320×240 5fps BGR"
echo "==> live branch: 원본 해상도·FPS 유지"
echo "==> 파이프라인 시작 (Ctrl+C 로 종료)"
echo ""

gst-launch-1.0 -v \
  filesrc location="$INPUT" ! \
  decodebin ! \
  videoconvert ! \
  tee name=t \
  \
  t. ! queue name=ai_queue leaky=downstream max-size-buffers=5 ! \
    videoscale ! \
    videorate ! \
    "video/x-raw,width=320,height=240,framerate=5/1" ! \
    videoconvert ! \
    "video/x-raw,format=BGR" ! \
    fakesink name=ai_sink sync=false \
  \
  t. ! queue name=live_queue max-size-buffers=0 max-size-time=0 max-size-bytes=0 ! \
    fakesink name=live_sink sync=false || true

echo ""
echo "==> 파이프라인 종료"
