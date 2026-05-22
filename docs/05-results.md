# 실험 결과: 로컬 vs 서버 환경 비교

> 측정 수집: `bash scripts/collect-metrics.sh [api_url] [seconds]`

## 측정 환경

### 로컬 (macOS, 개발)

| 항목 | 값 |
|------|-----|
| OS | macOS darwin arm64 (M1) |
| CPU | Apple M1 8코어 |
| 메모리 | 16GB |
| 입력 소스 | local file (sample.mp4) |
| GStreamer | Homebrew |

### 서버 (추후 기재)

| 항목 | 값 |
|------|-----|
| VM | — |
| OS | Ubuntu 22.04 |
| CPU | — |
| 메모리 | — |
| 입력 소스 | 브라우저 WHIP → MediaMTX RTSP |

---

## 측정 결과

### Branch FPS

| Branch | 목표 FPS | 로컬 실측 FPS | 서버 실측 FPS |
|--------|---------|-------------|-------------|
| live    | 30 | — | — |
| record  | 30 | — | — |
| ai      | 5  | — | — |
| preview | 5  | — | — |

### 시스템 자원

| 항목 | 로컬 | 서버 |
|------|------|------|
| GStreamer + FastAPI CPU | — | — |
| MediaPipe CPU | — | — |
| 전체 메모리 | — | — |

### HLS 재생 지연

| 환경 | 측정값 | 비고 |
|------|--------|------|
| 로컬 (파일 소스) | ~6초 | 3 × 2초 세그먼트 |
| 서버 (WHIP 송출) | — | 네트워크 지연 포함 |

### AI 동기화 오차

| 환경 | wall_clock_ms ↔ HLS 오차 | 비고 |
|------|--------------------------|------|
| 로컬 | — | programDateTime 필요 |
| 서버 | — | |

---

## 관찰 사항

### 로컬 테스트 (파일 소스)

- HLS 세그먼트 정상 생성 (`/tmp/hls/stream.m3u8`)
- MediaMTX RTSP/WHIP 포트 정상 응답
- FastAPI는 Ubuntu Dev Container 전용 (gi 의존성)

### 향후 개선 항목

1. `hlssink2`에 `program-date-time=true` 옵션 추가 → HLS-AI 동기화 정확도 향상
2. `rtspsrc`에 `retry-delay` 설정 → 송출 중단 시 자동 재연결
3. AI branch `leaky=downstream` + `drop=true` 이미 적용 → 처리 지연이 파이프라인에 영향 없음

---

## 프로젝트 회고

### 예상과 달랐던 것

- **GStreamer tee 백프레셔**: `leaky` 없이 AI branch를 연결하자마자 live branch가 즉시 멈췄다.
  `leaky=downstream`으로 해결했고, AI가 느려도 다른 branch에 전혀 영향이 없음을 확인했다.

- **MediaPipe LIVE_STREAM 타임스탬프 요구사항**: 타임스탬프가 단조 증가하지 않으면 `detect_async`가 프레임을 무시한다.
  `buf.pts == GST_CLOCK_TIME_NONE`인 프레임을 건너뛰는 방어 코드가 필요했다.

- **Python GI 바인딩 pip 불가**: `pip install gst-python`이 없다. `apt-get install python3-gst-1.0`이 필수이며,
  venv는 반드시 `--system-site-packages`로 생성해야 한다.

- **EAR 정규화 좌표계**: 픽셀 기반 EAR(0.25~0.35)과 달리, MediaPipe 정규화 좌표(0.0~1.0)로 계산한 EAR은
  0.15~0.20 범위다. 임계값을 데이터에 맞게 재조정해야 한다.

### 잘 된 것

- **4분기 파이프라인 설계**: live/record/ai/preview를 독립적으로 격리해 각 branch의 policy를 달리 적용한 구조가 실제로 잘 동작했다.
- **SSE EventBus**: GLib 스레드 ↔ asyncio 간 `run_coroutine_threadsafe` 패턴이 안정적으로 동작했다.
- **hls.js FRAG_CHANGED 동기화**: `wall_clock_ms` 기반 ±500ms 창 매핑 아이디어가 간단하면서 효과적이었다.

### 다음 시도해볼 것

1. `webrtcsink`(WHEP)로 live branch 지연을 < 1초로 낮추기
2. Prometheus + Grafana로 장기 메트릭 시각화
3. TURN 서버 추가로 NAT 환경에서도 WHIP 송출 보장
4. MediaPipe LIVE_STREAM → batch 처리로 throughput 향상 실험
