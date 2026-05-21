#!/usr/bin/env bash
# 개발 환경 전체 설정 스크립트 (Ubuntu 22.04)
# 새로운 VM 또는 Dev Container에서 최초 1회 실행한다.
# 사용법: bash scripts/dev-setup.sh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "==> GStreamer 설치"
bash "$SCRIPT_DIR/install-gstreamer.sh"

echo ""
echo "==> Python 가상환경 설정"
# --system-site-packages: python3-gst-1.0 은 pip 설치 불가 → 시스템 패키지를 venv 안에서 사용
python3 -m venv "$PROJECT_ROOT/.venv" --system-site-packages
echo "  가상환경 위치: $PROJECT_ROOT/.venv"
echo "  활성화: source .venv/bin/activate"

echo ""
echo "==> 개발 환경 설정 완료"
echo "  다음 단계: source .venv/bin/activate"
