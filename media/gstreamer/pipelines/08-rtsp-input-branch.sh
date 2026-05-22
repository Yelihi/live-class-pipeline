#!/usr/bin/env bash
# T-23: rtspsrc → 4-branch 파이프라인 (HLS / MKV / AI / Preview)
# 사전 조건: MediaMTX 실행 + 브라우저 WHIP 송출 중
# 사용: bash media/gstreamer/pipelines/08-rtsp-input-branch.sh [rtsp_url]
#       bash media/gstreamer/pipelines/08-rtsp-input-branch.sh rtsp://localhost:8554/room1
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
RTSP_URL="${1:-rtsp://localhost:8554/room1}"
HLS_DIR="${HLS_DIR:-/tmp/hls}"
OUTPUT_DIR="$PROJECT_ROOT/output"

mkdir -p "$HLS_DIR" "$OUTPUT_DIR"

echo "==> RTSP 입력: $RTSP_URL"
echo "==> HLS 출력: $HLS_DIR/stream.m3u8"
echo "==> MKV 출력: $OUTPUT_DIR/recording.mkv"
echo "==> 파이프라인 시작 (Ctrl+C 로 종료)"
echo ""

gst-launch-1.0 -v \
  rtspsrc location="$RTSP_URL" latency=200 ! \
  decodebin ! \
  videoconvert ! \
  tee name=t \
  \
  t. ! queue leaky=no name=live_q max-size-buffers=0 max-size-time=0 max-size-bytes=0 ! \
       videoconvert ! \
       x264enc tune=zerolatency bitrate=1500 speed-preset=ultrafast ! \
       hlssink2 \
         location="$HLS_DIR/segment%05d.ts" \
         playlist-location="$HLS_DIR/stream.m3u8" \
         target-duration=2 \
         max-files=10 \
  \
  t. ! queue leaky=no name=record_q max-size-buffers=0 max-size-time=0 max-size-bytes=0 ! \
       videoconvert ! \
       x264enc tune=zerolatency bitrate=2000 speed-preset=ultrafast ! \
       matroskamux ! \
       filesink location="$OUTPUT_DIR/recording.mkv" \
  \
  t. ! queue name=ai_q leaky=downstream max-size-buffers=5 ! \
       videoscale ! videorate ! \
       "video/x-raw,width=320,height=240,framerate=5/1" ! \
       videoconvert ! \
       "video/x-raw,format=BGR" ! \
       fakesink name=ai_sink sync=false \
  \
  t. ! queue name=preview_q leaky=downstream max-size-buffers=3 ! \
       videoscale ! \
       "video/x-raw,width=320,height=180" ! \
       fakesink name=preview_sink sync=false || true

echo ""
echo "==> 파이프라인 종료"
