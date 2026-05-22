#!/usr/bin/env bash
# T-15: HLS preview branch — hlssink2로 /tmp/hls에 세그먼트 저장
# HLS 파일을 FastAPI /hls/ 경로로 서빙하면 브라우저에서 재생 가능
# 사용: bash media/gstreamer/pipelines/07-hls-branch.sh [input.mp4]
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SAMPLE_MP4="$SCRIPT_DIR/../sample.mp4"
INPUT="${1:-$SAMPLE_MP4}"
HLS_DIR="${HLS_DIR:-/tmp/hls}"

mkdir -p "$HLS_DIR"

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
echo "==> HLS 출력: $HLS_DIR/stream.m3u8"
echo "==> 파이프라인 시작 (Ctrl+C 로 종료)"
echo ""

gst-launch-1.0 -v \
  filesrc location="$INPUT" ! \
  decodebin ! \
  videoconvert ! \
  tee name=t \
  \
  t. ! queue name=hls_queue max-size-buffers=0 max-size-time=0 max-size-bytes=0 ! \
       x264enc tune=zerolatency bitrate=1500 speed-preset=ultrafast ! \
       hlssink2 \
         location="$HLS_DIR/segment%05d.ts" \
         playlist-location="$HLS_DIR/stream.m3u8" \
         target-duration=2 \
         max-files=10 \
  \
  t. ! queue name=live_queue leaky=downstream max-size-buffers=5 ! \
       fakesink name=live_sink sync=false || true

echo ""
echo "==> HLS 파일 목록:"
ls -lh "$HLS_DIR"/ 2>/dev/null || echo "    (파일 없음)"
echo ""
echo "==> 파이프라인 종료"
