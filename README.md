# Live Class Pipeline Lab

GStreamer 기반 강의 스트림 분기 파이프라인 실험 프로젝트.

브라우저에서 수신한 WebRTC 스트림을 실시간으로 분기하여 HLS 송출 · 녹화 · AI 집중도 분석을 동시에 처리하는 파이프라인을 직접 구축하고 검증한다.

> 관련 이슈: [메인 실험 이슈 #1](https://github.com/Yelihi/live-class-pipeline/issues/1) · [태스크 로드맵 #2](https://github.com/Yelihi/live-class-pipeline/issues/2)

---

## 전체 아키텍처

```
[브라우저 강사]
     │ WebRTC (WHIP)
     ▼
┌─────────────────┐
│    MediaMTX     │  포트 8889 (WHIP 수신)
│                 │  포트 8554 (RTSP 내부 노출)
└────────┬────────┘
         │ RTSP pull
         ▼
┌─────────────────────────────────────────────────┐
│              GStreamer 파이프라인                 │
│                                                  │
│  rtspsrc → decodebin → videoconvert → tee ──────┤
│                                         │        │
│                          ┌──────────────┼──────────────────┐
│                          │              │                   │
│                    [live branch]  [record branch]    [ai branch]
│                    leaky queue    non-leaky queue    leaky queue
│                          │              │                   │
│                    x264enc         matroskamux         appsink
│                    hlssink2        filesink (MKV)          │
│                          │                            Python GI
└──────────────────────────┼────────────────────────────────┘
                           │                            │
                    [HLS 세그먼트]              [MediaPipe FaceLandmarker]
                           │                            │ 집중도 분석
                    ┌──────┴──────┐              [FastAPI SSE 이벤트]
                    │   nginx     │                     │
                    │  /hls/*     │              ┌──────┴──────┐
                    └──────┬──────┘              │  대시보드   │
                           │ HLS                 │  (React)    │
                    [브라우저 시청자]             └─────────────┘
                    hls.js 플레이어
```

**시간 동기화 전략**: AI 분석 결과(`wall_clock_ms`)와 HLS 재생 위치(`programDateTime`)를 ±500ms 윈도우로 매핑하여 스트림 지연과 무관하게 정확한 집중도 오버레이를 표시한다.

---

## 디렉토리 구조

```
live-class-pipeline-lab/
├── apps/
│   ├── dashboard/        # Phase 3 — React + hls.js 대시보드
│   └── control-api/      # Phase 2 — FastAPI 파이프라인 제어 서버
├── media/
│   ├── gstreamer/
│   │   ├── pipelines/    # Phase 1 — gst-launch-1.0 실험 스크립트 (.sh)
│   │   └── python/       # Phase 2 — Python GI 바인딩 파이프라인 제어
│   └── mediamtx/         # Phase 4 — MediaMTX mediamtx.yml 설정
├── infra/
│   ├── docker/           # Phase 5 — 각 서비스 Dockerfile
│   ├── compose/          # Phase 5 — docker-compose 파일
│   └── proxy/            # Phase 5 — Caddy 리버스 프록시 설정
├── docs/                 # 실험 계획 및 결과 문서
├── scripts/
│   └── dev-setup.sh      # T-01에서 GStreamer apt 설치 내용 채움
├── .gitignore
└── README.md
```

### 파이프라인 스크립트 파일명 컨벤션

`media/gstreamer/pipelines/` 안의 파일은 `t{번호}_{설명}.sh` 형식으로 저장한다.

예: `t01_install_verify.sh`, `t02_basic_pipeline.sh`, `t04_tee_leaky_queue.sh`

---

## Phase별 진행 현황

| Phase | 내용 | 상태 |
|-------|------|------|
| Phase 0 | 프로젝트 초기화 (T-00) | 🟡 진행 중 |
| Phase 1 | GStreamer 파이프라인 실험 (T-01~T-08) | ⬜ 대기 |
| Phase 2 | FastAPI 제어 서버 + SSE (T-09~T-13) | ⬜ 대기 |
| Phase 3 | React 대시보드 (T-14~T-16) | ⬜ 대기 |
| Phase 4 | MediaPipe AI 집중도 분석 (T-17~T-22) | ⬜ 대기 |
| Phase 5 | Docker 컨테이너화 (T-23~T-28) | ⬜ 대기 |
| Phase 6 | 서버 배포 + E2E 검증 (T-29~T-31) | ⬜ 대기 |

---

## 기술 스택

| 역할 | 기술 |
|------|------|
| 스트림 수신 | MediaMTX (WHIP → RTSP) |
| 파이프라인 | GStreamer 1.0 (apt, Ubuntu 22.04) |
| AI 분석 | Google MediaPipe FaceLandmarker |
| 제어 서버 | FastAPI + Python GI 바인딩 |
| 대시보드 | React + hls.js |
| 배포 | Docker Compose + Caddy |

---

## 실행 방법

> Phase 5 이후 채워집니다.

```bash
# 개발 환경 설정 (T-01에서 구현)
./scripts/dev-setup.sh

# 서비스 실행 (T-27에서 구현)
# docker compose -f infra/compose/docker-compose.local.yml up
```

---

## 핵심 설계 결정

- **녹화 포맷: MKV** — MP4는 비정상 종료 시 파일 손상. `matroskamux`는 스트리밍 방식으로 기록하여 크래시에 안전
- **tee 백프레셔 전략: leaky queue** — AI/HLS branch는 `queue leaky=downstream`으로 느린 처리가 전체 파이프라인을 막지 않게 격리
- **Python-GStreamer 통합: in-process** — FastAPI + GLib MainLoop를 같은 프로세스에서 실행, `threading.Thread`로 GLib MainLoop 분리
- **시청자 전달: HLS** — `hlssink2`로 세그먼트 생성, nginx로 서빙. 지연 3~10초 허용
