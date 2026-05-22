#!/usr/bin/env bash
# T-03: tee 기반 4분기 파이프라인 — live / record / ai / preview
# 사용: bash media/gstreamer/pipelines/02-four-branch.sh [input.mp4]
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

gst-launch-1.0 -v \
  filesrc location="$INPUT" ! \
  decodebin ! \
  videoconvert ! \
  tee name=t \
  t. ! queue name=live_queue ! videoconvert ! fakesink name=live_sink sync=false \
  t. ! queue name=record_queue ! videoconvert ! fakesink name=record_sink sync=false \
  t. ! queue name=ai_queue ! videoconvert ! fakesink name=ai_sink sync=false \
  t. ! queue name=preview_queue ! videoconvert ! fakesink name=preview_sink sync=false || true

echo ""
echo "==> 파이프라인 종료"
