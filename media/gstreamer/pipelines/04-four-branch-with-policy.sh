#!/usr/bin/env bash
# T-04: tee 4분기 파이프라인 — branch별 queue 정책 적용
# live/record : non-leaky, 무제한 버퍼 (데이터 유실 없음)
# ai/preview  : leaky=downstream, max-size-buffers=5 (최신 프레임만 처리)
# 사용: bash media/gstreamer/pipelines/04-four-branch-with-policy.sh [input.mp4]
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
echo "==> 파이프라인 시작 (Ctrl+C 로 종료)"
echo ""

gst-launch-1.0 -v \
  filesrc location="$INPUT" ! \
  decodebin ! \
  videoconvert ! \
  tee name=t \
  t. ! queue name=live_queue max-size-buffers=0 max-size-time=0 max-size-bytes=0 ! videoconvert ! fakesink name=live_sink sync=false \
  t. ! queue name=record_queue max-size-buffers=0 max-size-time=0 max-size-bytes=0 ! videoconvert ! fakesink name=record_sink sync=false \
  t. ! queue name=ai_queue leaky=downstream max-size-buffers=5 ! videoconvert ! fakesink name=ai_sink sync=false \
  t. ! queue name=preview_queue leaky=downstream max-size-buffers=5 ! videoconvert ! fakesink name=preview_sink sync=false || true

echo ""
echo "==> 파이프라인 종료"
