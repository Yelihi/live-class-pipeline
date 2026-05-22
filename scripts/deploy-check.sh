#!/usr/bin/env bash
# T-29: 배포 상태 확인 스크립트
# 사용: bash scripts/deploy-check.sh [domain]
#       bash scripts/deploy-check.sh your-domain.com
set -euo pipefail

DOMAIN="${1:-localhost}"
API_BASE="https://$DOMAIN"
MTX_API="http://localhost:9997"

if [[ "$DOMAIN" == "localhost" ]]; then
  API_BASE="http://localhost:8000"
fi

echo "=== 배포 상태 확인: $DOMAIN ==="
echo ""

pass=0; fail=0

check() {
  local desc="$1" cmd="$2"
  if eval "$cmd" &>/dev/null; then
    echo "  ✓ $desc"
    ((pass++)) || true
  else
    echo "  ✗ $desc"
    ((fail++)) || true
  fi
}

echo "1. HTTP(S) 엔드포인트"
check "대시보드 접근 ($API_BASE)" \
  "curl -sf -o /dev/null -w '%{http_code}' '$API_BASE' | grep -qE '200|301|302'"
check "API /health" \
  "curl -sf '$API_BASE/health' | python3 -c \"import sys,json; d=json.load(sys.stdin); sys.exit(0 if d.get('status')=='ok' else 1)\""
check "API /pipeline/status" \
  "curl -sf '$API_BASE/pipeline/status'"
check "API /metrics" \
  "curl -sf '$API_BASE/metrics'"

echo ""
echo "2. MediaMTX"
check "MediaMTX API (localhost:9997)" \
  "curl -sf '$MTX_API/v3/paths/list'"
check "room1 경로 등록" \
  "curl -sf '$MTX_API/v3/paths/list' | python3 -c \"import sys,json; d=json.load(sys.stdin); sys.exit(0 if any(p['name']=='room1' for p in d.get('items',[])) else 1)\""

echo ""
echo "3. Docker 서비스"
if command -v docker &>/dev/null; then
  check "api 컨테이너 실행 중" \
    "docker ps --format '{{.Names}}' | grep -q api"
  check "mediamtx 컨테이너 실행 중" \
    "docker ps --format '{{.Names}}' | grep -q mediamtx"
  check "dashboard 컨테이너 실행 중" \
    "docker ps --format '{{.Names}}' | grep -q dashboard"
else
  echo "  (docker 없음 — 로컬 프로세스 실행 가정)"
fi

echo ""
echo "=== 결과: ${pass}개 통과 / $((pass + fail))개 검사 ==="
[[ $fail -eq 0 ]] && echo "모든 검사 통과" || echo "${fail}개 실패"
exit $fail
