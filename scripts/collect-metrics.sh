#!/usr/bin/env bash
# T-38: 메트릭 수집 스크립트 — 단일/다중 룸 포맷 자동 감지
# 사용: bash scripts/collect-metrics.sh [api_url] [seconds] [output_csv]
#       bash scripts/collect-metrics.sh http://localhost:8000 30 results/gst_n1.csv
set -euo pipefail

API_BASE="${1:-http://localhost:8000}"
DURATION="${2:-30}"
OUTPUT="${3:-/dev/stdout}"

mkdir -p "$(dirname "$OUTPUT")" 2>/dev/null || true

echo "==> 측정 시작: $OUTPUT (${DURATION}초, ${API_BASE})"

echo "timestamp,live_fps,record_fps,ai_fps,preview_fps" > "$OUTPUT"

for i in $(seq 1 "$DURATION"); do
  TIMESTAMP=$(date -u +%Y-%m-%dT%H:%M:%SZ)
  SNAPSHOT=$(curl -sf "${API_BASE}/metrics" 2>/dev/null || echo 'null')

  python3 - "$TIMESTAMP" "$SNAPSHOT" "$OUTPUT" <<'PYEOF'
import json, sys

ts, raw, outfile = sys.argv[1], sys.argv[2], sys.argv[3]
branches = ["live", "record", "ai", "preview"]

try:
    d = json.loads(raw)
except Exception:
    d = {}

if "aggregate" in d:
    agg = d["aggregate"]
    vals = [str(agg.get(b, {}).get("avg_fps", 0)) for b in branches]
else:
    vals = [str(d.get(b, {}).get("fps", 0)) for b in branches]

with open(outfile, "a") as f:
    f.write(f"{ts},{','.join(vals)}\n")
PYEOF

  printf "\r  %d/%d 수집 중..." "$i" "$DURATION"
  sleep 1
done

echo ""
echo "==> 완료: $OUTPUT"
echo ""
echo "==> 요약:"
python3 - "$OUTPUT" <<'PYEOF'
import sys, csv

rows = []
with open(sys.argv[1]) as f:
    reader = csv.DictReader(f)
    for row in reader:
        rows.append(row)

if not rows:
    print("  데이터 없음"); sys.exit(0)

print(f"  수집 샘플: {len(rows)}개")
for col in ["live_fps", "record_fps", "ai_fps", "preview_fps"]:
    vals = [float(r[col]) for r in rows if float(r[col]) > 0]
    if vals:
        print(f"  {col:<14} 평균: {sum(vals)/len(vals):.1f}  (min {min(vals):.1f} / max {max(vals):.1f})")
    else:
        print(f"  {col:<14} 데이터 없음")
PYEOF
