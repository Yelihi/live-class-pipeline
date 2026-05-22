#!/usr/bin/env bash
# T-30: 측정 지표 수집 스크립트 (60초간 1초 간격)
# 사용: bash scripts/collect-metrics.sh [api_base_url] [duration_seconds]
#       bash scripts/collect-metrics.sh http://localhost:8000 60
set -euo pipefail

API_BASE="${1:-http://localhost:8000}"
DURATION="${2:-60}"
OUTPUT_DIR="docs/measurements"
OUTPUT="$OUTPUT_DIR/$(date +%Y%m%d_%H%M%S).jsonl"

mkdir -p "$OUTPUT_DIR"
echo "==> 측정 시작: $OUTPUT (${DURATION}초)"
echo ""

for i in $(seq 1 "$DURATION"); do
  TIMESTAMP=$(date -u +%Y-%m-%dT%H:%M:%SZ)
  API_METRICS=$(curl -sf "$API_BASE/metrics" 2>/dev/null || echo 'null')

  if command -v docker &>/dev/null; then
    DOCKER_STATS=$(docker stats --no-stream --format \
      '{"name":"{{.Name}}","cpu":"{{.CPUPerc}}","mem":"{{.MemUsage}}"}' \
      2>/dev/null | python3 -c "import sys,json; lines=[json.loads(l) for l in sys.stdin if l.strip()]; print(json.dumps(lines))")
  else
    DOCKER_STATS='[]'
  fi

  printf '{"ts":"%s","api":%s,"docker":%s}\n' \
    "$TIMESTAMP" "$API_METRICS" "$DOCKER_STATS" >> "$OUTPUT"

  printf "\r  %d/%d 수집 중..." "$i" "$DURATION"
  sleep 1
done

echo ""
echo "==> 완료: $OUTPUT"
echo ""
echo "==> 요약:"
python3 - "$OUTPUT" <<'PYEOF'
import sys, json

lines = []
with open(sys.argv[1]) as f:
    for line in f:
        try:
            lines.append(json.loads(line))
        except json.JSONDecodeError:
            pass

if not lines:
    print("  데이터 없음")
    sys.exit(0)

branches = ["live", "record", "ai", "preview"]
fps_sums = {b: [] for b in branches}

for item in lines:
    api = item.get("api") or {}
    for b in branches:
        fps = api.get(b, {}).get("fps", 0)
        if fps > 0:
            fps_sums[b].append(fps)

print(f"  수집 샘플: {len(lines)}개")
for b in branches:
    vals = fps_sums[b]
    if vals:
        avg = sum(vals) / len(vals)
        print(f"  {b:<8} FPS 평균: {avg:.1f}")
    else:
        print(f"  {b:<8} FPS: 데이터 없음")
PYEOF
