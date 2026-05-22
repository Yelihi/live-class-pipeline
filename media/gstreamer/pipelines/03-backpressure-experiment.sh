#!/usr/bin/env bash
# T-04: backpressure 실험 — leaky vs non-leaky queue
# 사용: bash media/gstreamer/pipelines/03-backpressure-experiment.sh [no-leaky|leaky]
set -euo pipefail

MODE="${1:-}"

if [[ "$MODE" != "no-leaky" && "$MODE" != "leaky" ]]; then
  echo "사용법: $0 [no-leaky|leaky]"
  echo "  no-leaky  — AI branch 지연이 live branch를 블락하는 현상 확인"
  echo "  leaky     — leaky queue 적용 후 live branch 정상 동작 확인"
  exit 1
fi

echo "==> 실험 모드: $MODE"
echo "==> videotestsrc 10프레임 사용 (Ctrl+C 로 강제 종료 가능)"
echo ""

if [[ "$MODE" == "no-leaky" ]]; then
  echo "==> [실험 1] non-leaky queue — AI branch 0.5초 지연 적용"
  echo "==> live branch도 0.5초마다 블락되는지 관찰"
  echo ""
  gst-launch-1.0 -v \
    videotestsrc num-buffers=10 ! tee name=t \
    t. ! queue name=live_q ! identity name=live_identity ! fakesink name=live_sink sync=false \
    t. ! queue name=ai_q ! identity sleep-time=500000000 name=ai_identity ! fakesink name=ai_sink sync=false || true
else
  echo "==> [실험 2] leaky queue — AI branch에만 leaky 적용"
  echo "==> live branch는 정상 속도, ai branch만 느리게 처리되는지 관찰"
  echo ""
  gst-launch-1.0 -v \
    videotestsrc num-buffers=10 ! tee name=t \
    t. ! queue name=live_q ! identity name=live_identity ! fakesink name=live_sink sync=false \
    t. ! queue name=ai_q leaky=downstream max-size-buffers=3 ! \
       identity sleep-time=500000000 name=ai_identity ! fakesink name=ai_sink sync=false || true
fi

echo ""
echo "==> 실험 종료"
