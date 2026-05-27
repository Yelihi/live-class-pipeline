#!/usr/bin/env bash
# T-33: N개 합성 RTSP 스트림 생성기
# 사용: bash scripts/gen-streams.sh [N] [RTSP_BASE_URL]
#       bash scripts/gen-streams.sh 4 rtsp://localhost:8554
set -euo pipefail

N=${1:-4}
RTSP_BASE=${2:-"rtsp://localhost:8554"}

command -v ffmpeg >/dev/null 2>&1 || { echo "[gen-streams] ERROR: ffmpeg not found"; exit 1; }

# drawtext 필터 지원 여부 감지 (libfreetype 필요)
if ffmpeg -filters 2>/dev/null | grep -q drawtext; then
  HAS_DRAWTEXT=1
else
  HAS_DRAWTEXT=0
fi

pids=()

for i in $(seq 1 "$N"); do
  if [ "$HAS_DRAWTEXT" -eq 1 ]; then
    INPUT="testsrc2=size=1280x720:rate=30,drawtext=text='Room${i}':fontsize=80:x=50:y=50:fontcolor=white"
  else
    INPUT="testsrc2=size=1280x720:rate=30"
  fi

  ffmpeg -re \
    -f lavfi \
    -i "${INPUT}" \
    -c:v libx264 \
    -preset ultrafast \
    -tune zerolatency \
    -b:v 1000k \
    -rtsp_transport tcp \
    -f rtsp "${RTSP_BASE}/room${i}" \
    -loglevel error &

  pids+=($!)
  echo "[gen-streams] room${i} → ${RTSP_BASE}/room${i} (PID $!)"
done

echo "[gen-streams] Streaming ${N} room(s). Press Ctrl+C to stop."
trap 'echo "[gen-streams] Stopping..."; kill "${pids[@]}" 2>/dev/null; wait; exit 0' INT TERM
wait
