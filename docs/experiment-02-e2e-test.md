# Experiment 02 — End-to-End 테스트

## 테스트 일시: 2026-05-22

## 아키텍처

```
[브라우저 카메라]
      │ WHIP (WebRTC)
      ▼
  MediaMTX (:8889 WHIP / :8554 RTSP)
      │ RTSP pull
      ▼
 GStreamer rtspsrc
      │
      tee
     ╱╲╱╲
    live  record  ai         preview
    (HLS) (MKV)  (appsink   (fakesink)
                 → MediaPipe
                 → FastAPI SSE)
      │                   │
  /tmp/hls/           EventBus
  stream.m3u8             │
      │                   ▼
      └──────── React 대시보드
                (HLS Player + AI 패널)
```

## 테스트 환경

- OS: macOS darwin arm64 (M1)
- GStreamer: 1.x (Homebrew)
- MediaMTX: v1.18.2
- Python: FastAPI (Dev Container에서 실행)
- 브라우저: Chrome

## 실행 순서

```bash
# 터미널 1: MediaMTX
bash scripts/start-mediamtx.sh

# 터미널 2: GStreamer (파일 소스 테스트 / 또는 RTSP)
bash media/gstreamer/pipelines/08-rtsp-input-branch.sh
# (Dev Container) FastAPI:
# cd apps/control-api && uvicorn src.main:app --port 8000

# 터미널 3: React 대시보드
cd apps/dashboard && npm run dev

# 브라우저: http://localhost:5173 접속 → 송출 탭 → 송출 시작
```

## 검증 결과

### 파일 소스 테스트 (macOS 로컬)

| 항목 | 결과 |
|------|------|
| MediaMTX 실행 | ✅ RTSP:8554 / WHIP:8889 / API:9997 |
| `curl /v3/paths/list` room1 응답 | ✅ |
| `07-hls-branch.sh` HLS 파일 생성 | ✅ segment × 5 + stream.m3u8 |
| HLS 세그먼트 재생 (`decodebin ! fakesink`) | ✅ |
| React 앱 빌드 (`npm run build`) | ✅ TypeScript 오류 없음 |

### RTSP 연동 (Dev Container 전용)

FastAPI + gi 바인딩은 Ubuntu Dev Container에서 실행 필요.
아래 항목은 Dev Container 환경에서 검증.

| 항목 | 예상 결과 |
|------|-----------|
| WHIP POST → MediaMTX 연결 수립 | room1 readyTime 설정됨 |
| GStreamer rtspsrc pull | 4개 branch 동작 |
| `GET /metrics` live FPS | ~30fps |
| `GET /metrics` ai FPS | ~5fps |
| SSE `ai_result` 이벤트 | 5fps로 수신 |
| HLS player 재생 | 2~6초 지연 후 재생 |
| AI 집중도 패널 | attention_score 0~1.0 표시 |

## 측정값 (파일 소스 기준)

| 지표 | 값 |
|------|----|
| HLS 세그먼트 크기 | ~380KB / 2초 |
| HLS 총 지연 | ~6초 (3 세그먼트 × 2초) |
| AI 분석 FPS | 5fps (videorate 제한) |
| CPU 사용률 | 미측정 (Dev Container 필요) |

## 관찰된 이슈

### macOS 로컬

- gi 모듈 없어 FastAPI AI 경로 실행 불가 → Dev Container 전용으로 명시
- GStreamer videotestsrc 기반 sample.mp4는 얼굴 없어 AI 결과 `face_detected: false`

### 향후 개선 항목

- `rtspsrc` 연결 끊김 시 자동 재연결 (`do-retransmission=false`, retry loop)
- AI branch 처리 속도가 느릴 때 `drop=true`로 최신 프레임만 처리 (이미 적용됨)
- HLS `program-date-time=true` 옵션으로 시간 동기화 정확도 개선
