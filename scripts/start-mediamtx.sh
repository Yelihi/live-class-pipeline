#!/usr/bin/env bash
# T-21: MediaMTX 실행 스크립트
# 설치 (Ubuntu/Dev Container):
#   wget -O /tmp/mediamtx.tar.gz \
#     https://github.com/bluenviron/mediamtx/releases/latest/download/mediamtx_linux_amd64.tar.gz
#   tar -xzf /tmp/mediamtx.tar.gz -C /usr/local/bin/
#
# 설치 (macOS/Homebrew):
#   brew install mediamtx
#
# 포트:
#   RTSP  : 8554  (GStreamer rtspsrc)
#   WHIP  : 8889  (브라우저 WebRTC 송출)
#   API   : 9997  (curl http://localhost:9997/v3/paths/list)
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
CONFIG="$PROJECT_ROOT/media/mediamtx/mediamtx.yml"

if ! command -v mediamtx &>/dev/null; then
  echo "오류: mediamtx 바이너리를 찾을 수 없습니다."
  echo "Ubuntu: wget + tar -C /usr/local/bin/ 로 설치하세요."
  echo "macOS:  brew install mediamtx"
  exit 1
fi

echo "==> MediaMTX 시작"
echo "==> 설정: $CONFIG"
echo "==> RTSP : rtsp://localhost:8554/room1"
echo "==> WHIP : http://localhost:8889/room1/whip"
echo "==> API  : http://localhost:9997/v3/paths/list"
echo ""

exec mediamtx "$CONFIG"
