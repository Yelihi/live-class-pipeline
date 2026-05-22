#!/usr/bin/env bash
# T-05: record branch MKV 파일 저장 검증
# MODE=single (기본): x264enc → matroskamux → filesink
# MODE=split        : x264enc → splitmuxsink (matroskamux, MAX_SEGMENT_TIME 단위 분할)
# 사용: bash media/gstreamer/pipelines/05-record-branch.sh [input.mp4]
#       MODE=split MAX_SEGMENT_TIME=10000000000 bash media/gstreamer/pipelines/05-record-branch.sh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
SAMPLE_MP4="$SCRIPT_DIR/../sample.mp4"
INPUT="${1:-$SAMPLE_MP4}"
OUTPUT_DIR="$PROJECT_ROOT/output"
MODE="${MODE:-single}"
# 기본값: 600초(10분) = 600_000_000_000 ns. 테스트 시 10s=10_000_000_000 등으로 오버라이드
MAX_SEGMENT_TIME="${MAX_SEGMENT_TIME:-600000000000}"

mkdir -p "$OUTPUT_DIR"

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
echo "==> MODE: $MODE"
echo "==> 출력 디렉토리: $OUTPUT_DIR"
echo ""

if [[ "$MODE" == "split" ]]; then
  SEGMENT_SEC=$(( MAX_SEGMENT_TIME / 1000000000 ))
  echo "==> splitmuxsink 분할 녹화 시작 (세그먼트 ${SEGMENT_SEC}초)"
  echo "==> Ctrl+C 로 종료"
  echo ""
  gst-launch-1.0 -v \
    filesrc location="$INPUT" ! \
    decodebin ! \
    videoconvert ! \
    x264enc tune=zerolatency bitrate=2000 speed-preset=ultrafast ! \
    splitmuxsink \
      location="$OUTPUT_DIR/segment_%02d.mkv" \
      muxer-factory=matroskamux \
      max-size-time="$MAX_SEGMENT_TIME" || true
  echo ""
  echo "==> 분할 파일 목록:"
  ls -lh "$OUTPUT_DIR"/segment_*.mkv 2>/dev/null || echo "    (파일 없음)"
else
  echo "==> 단일 MKV 녹화 시작"
  echo "==> Ctrl+C 로 종료"
  echo ""
  gst-launch-1.0 -v \
    filesrc location="$INPUT" ! \
    decodebin ! \
    videoconvert ! \
    x264enc tune=zerolatency bitrate=2000 speed-preset=ultrafast ! \
    matroskamux ! \
    filesink location="$OUTPUT_DIR/recording.mkv" || true
  echo ""
  echo "==> 생성된 파일:"
  ls -lh "$OUTPUT_DIR/recording.mkv" 2>/dev/null || echo "    (파일 없음)"
fi

echo ""
echo "==> 파이프라인 종료"
