# Live Class Pipeline Lab

> GStreamer 기반 실시간 강의 스트림 분기 파이프라인 — 기술 실증 프로젝트

브라우저에서 수신한 WebRTC 스트림을 실시간으로 4개 branch로 분기하여 HLS 송출 · 녹화 · AI 집중도 분석을 동시에 처리하는 파이프라인을 직접 구축하고 검증합니다.

---

## 아키텍처

```mermaid
graph TD
    subgraph Browser["브라우저"]
        CAM[카메라]
        PUB[Publisher Page<br/>WHIP 송출]
        DASH[Operator Dashboard<br/>React + hls.js]
    end

    subgraph Ingest["Media Ingest"]
        MTX[MediaMTX<br/>WHIP → RTSP 변환]
    end

    subgraph GST["GStreamer Pipeline"]
        SRC[rtspsrc]
        TEE[tee 4분기]
        LB[Live Branch<br/>HLS hlssink2]
        RB[Record Branch<br/>MKV matroskamux]
        AB[AI Branch<br/>320×240 5fps BGR appsink]
        PB[Preview Branch<br/>320×240 5fps fakesink]
    end

    subgraph AILayer["AI Worker"]
        MP[MediaPipe FaceLandmarker]
        AT[EAR 계산 + Attention Score]
    end

    subgraph API["FastAPI Control API"]
        CTRL[Pipeline start/stop]
        METRICS[Pad Probe 메트릭]
        SSE[SSE EventBus]
    end

    CAM -->|getUserMedia| PUB
    PUB -->|WHIP POST| MTX
    MTX -->|RTSP pull| SRC
    SRC --> TEE
    TEE --> LB & RB & AB & PB
    LB -->|stream.m3u8| DASH
    AB --> MP --> AT -->|ai_result event| SSE
    METRICS -->|metrics event 1fps| SSE
    SSE -->|EventSource| DASH
    CTRL -.->|제어| GST
```

---

## 핵심 검증 내용

1. **GStreamer tee** — 단일 입력을 4개 branch로 무손실 분기
2. **백프레셔 격리** — AI branch `leaky=downstream`으로 느린 처리가 live branch에 영향 없음
3. **MediaPipe LIVE_STREAM** — 5fps 실시간 얼굴 랜드마크 추출 + EAR 기반 집중도 산출
4. **HLS-AI 동기화** — `wall_clock_ms` + hls.js `FRAG_CHANGED`로 재생 시간 ±500ms 매핑
5. **전체 스택 Docker화** — GStreamer + FastAPI + React + MediaMTX + Caddy TLS

---

## 실험 결과 요약

| 항목 | 결과 |
|------|------|
| AI branch FPS | 5fps (videorate 제한, 설계 목표 달성) |
| live branch FPS | 30fps (AI branch와 독립) |
| HLS 재생 지연 | ~6초 (2초 × 3 세그먼트) |
| EAR 측정 (정면 얼굴) | 0.16~0.18 (정규화 좌표계) |
| attention_score 범위 | 0.0~1.0 정상 출력 |

> 상세: [docs/experiment-02-e2e-test.md](docs/experiment-02-e2e-test.md) · [docs/05-results.md](docs/05-results.md)

---

## 실행 방법

### 로컬 (Docker Compose)

```bash
docker compose -f infra/compose/docker-compose.local.yml up --build
# Dashboard: http://localhost:3000
# API:       http://localhost:8000
# MediaMTX:  rtsp://localhost:8554/room1
```

### 서버 배포 (Caddy + TLS)

```bash
cp infra/compose/.env.server.example infra/compose/.env.server
# .env.server에 DOMAIN=your-domain.com 설정 후:
DOMAIN=your-domain.com docker compose \
  -f infra/compose/docker-compose.server.yml up -d --build
```

### 로컬 개발 (파일 소스)

```bash
# MediaMTX
bash scripts/start-mediamtx.sh

# GStreamer HLS (파일 소스)
bash media/gstreamer/pipelines/07-hls-branch.sh

# React 대시보드
cd apps/dashboard && npm run dev
```

---

## 태스크 진행 현황

| Phase | 범위 | 상태 |
|-------|------|------|
| Phase 1 | GStreamer 파이프라인 기초 (T01~T06) | ✅ 완료 |
| Phase 2 | FastAPI + Python GI 연동 (T07~T10) | ✅ 완료 |
| Phase 3 | React Dashboard + SSE (T11~T15) | ✅ 완료 |
| Phase 4 | MediaPipe AI 분석 (T16~T20) | ✅ 완료 |
| Phase 5 | MediaMTX WHIP 연동 (T21~T24) | ✅ 완료 |
| Phase 6 | Docker 배포 (T25~T29) | ✅ 완료 |
| Phase 7 | 측정 및 보고서 (T30~T31) | ✅ 완료 |

---

## 기술 스택

| 레이어 | 기술 |
|--------|------|
| 미디어 파이프라인 | GStreamer 1.x, tee, hlssink2, matroskamux, appsink |
| 미디어 서버 | MediaMTX (WHIP ingest, RTSP relay) |
| AI 분석 | Google MediaPipe FaceLandmarker, EAR 알고리즘 |
| 백엔드 | FastAPI, uvicorn, Python GI 바인딩, SSE EventBus |
| 프론트엔드 | React 18, Vite, TypeScript, Tailwind CSS, hls.js, Recharts |
| 인프라 | Docker Compose, Caddy (자동 TLS), Nginx (SPA 서빙) |

---

> 관련 이슈: [태스크 로드맵 #2](https://github.com/Yelihi/live-class-pipeline/issues/2)
