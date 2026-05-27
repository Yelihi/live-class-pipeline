# 실험 결과: 로컬 vs 서버 환경 비교

> 측정 수집: `bash scripts/collect-metrics.sh [api_url] [seconds]`

## 측정 환경

### 로컬 (macOS, Docker)

| 항목 | 값 |
|------|-----|
| OS | macOS darwin arm64 (M1) |
| CPU | Apple M1 8코어 |
| 메모리 | 16GB |
| 입력 소스 | 브라우저 WHIP → MediaMTX RTSP |
| 실행 방식 | docker-compose.local.yml |
| Preview 방식 | WebRTC WHEP (MediaMTX 내장) |

### 서버 (추후 기재)

| 항목 | 값 |
|------|-----|
| VM | — |
| OS | Ubuntu 22.04 |
| CPU | — |
| 메모리 | — |
| 입력 소스 | 브라우저 WHIP → MediaMTX RTSP |
| Preview 방식 | WebRTC WHEP |

---

## 측정 결과

### Branch FPS

| Branch | 목표 FPS | 로컬 실측 FPS | 총 프레임 | 서버 실측 FPS |
|--------|---------|-------------|---------|-------------|
| live    | 30 | **30.3** | 805 | — |
| record  | 30 | **30.3** | 805 | — |
| ai      | 5  | **5.0**  | 144 | — |
| preview | 5  | **5.0**  | 144 | — |

> 측정 시점: 2026-05-22, 로컬 Docker 스택 (브라우저 WHIP 카메라 입력 기준)
>
> live·record는 목표 30fps 대비 오차 1% 이내. ai·preview는 5fps 상한 정확히 준수.

### 시스템 자원

| 항목 | 로컬 | 서버 |
|------|------|------|
| GStreamer + FastAPI CPU | — | — |
| MediaPipe CPU | — | — |
| 전체 메모리 | — | — |

### Preview 지연 (방식별 비교)

| 방식 | 지연 | 비고 |
|------|------|------|
| HLS (이전) | ~6초 | 3 × 2초 세그먼트 버퍼링 |
| WebRTC WHEP (현재) | < 100ms | MediaMTX 내장 WHEP 엔드포인트 |

> WHEP 전환 배경: `React.memo`로 HLS 리렌더를 막자 플레이어가 정적으로 굳는 문제 발생.
> 근본 원인이 HLS의 세그먼트 방식에 있었으므로 WebRTC로 전면 교체.

### AI 동기화

| 방식 | 동기화 전략 | 오차 |
|------|-----------|------|
| HLS + `wall_clock_ms` (이전) | `FRAG_CHANGED.programDateTime` ↔ AI 타임스탬프 ±500ms 창 | ~300ms 추정 |
| WHEP 실시간 (현재) | 동기화 불필요 — 영상·AI 결과 모두 실시간 | 0 |

---

## 다중 스트림 비교 (GStreamer vs OpenCV)

> T-32 ~ T-38 실험: 동일한 4-branch 출력을 GStreamer(C 네이티브)와 OpenCV+Python 스레딩으로 구현하여 N룸 동시 처리 성능을 비교한다.

### 실험 조건

| 항목 | 값 |
|------|-----|
| 하드웨어 | macOS darwin arm64 (Apple M1, 8코어, 16GB) |
| 입력 소스 | `scripts/gen-streams.sh` — testsrc2 1280×720 30fps, H.264 1000kbps |
| 측정 시간 | 30초 |
| 측정 스크립트 | `scripts/collect-metrics.sh` |
| 측정 시점 | 2026-05-27 |

### live branch avg_fps (목표: 30fps)

| 스트림 수 | GStreamer avg | GStreamer 지터 | OpenCV avg | OpenCV 지터 |
|---------|-------------|--------------|-----------|------------|
| N=1     | **30.0** fps | σ=0 (min=max=30.0) | **31.1** fps | σ=6 (min 30.0 / max 48.7) |
| N=4     | **30.3** fps | σ=0.36 (min 30.0 / max 31.1) | **5.9** fps | σ=4.80 (min 1.1 / max 21.5) |

> 샘플 수: GStreamer N=1 30개, N=4 30개 / OpenCV N=1 44개, N=4 30개
>
> 측정 시점: N=4 재측정 2026-05-27

### ai branch avg_fps (목표: 5fps)

| 스트림 수 | GStreamer | OpenCV |
|---------|----------|--------|
| N=1     | **5.0** fps (σ=0) | **4.9** fps (min 3.3 / max 5.0) |
| N=4     | **5.0** fps (σ=0) | **6.2** fps (σ=5.03 / min 1.1 / max 20.1) |

> OpenCV N=4의 ai_fps가 목표(5fps)를 소폭 초과하고 live_fps와 유사한 것은
> 캡처 자체가 ~6fps로 제한되어 AI_INTERVAL(0.2s) 체크가 거의 항상 통과되기 때문이다.

### 핵심 발견: N=4에서의 실제 처리량 격차

N=4 재측정 결과, 두 버전의 차이는 "지터" 수준이 아니라 **처리량 자체의 붕괴**였다.

| 특성 | GStreamer | OpenCV + Python threads |
|------|----------|------------------------|
| live fps (N=4) | **30.3 fps** (목표 달성) | **5.9 fps** (목표의 20%) |
| fps 안정성 | σ=0.36 — C 레벨 PTS 기반 | σ=4.80 — 극심한 불안정 |
| 프레임 전달 방식 | zero-copy (참조 카운팅) | `frame.copy()` × 4 × N |
| 5fps 제어 | `videorate` C 레벨 | `time.monotonic()` 수동 샘플링 |
| AI 격리 | `leaky=downstream` C 큐 | Python `Queue(maxsize=5)` + GIL |
| RTSP 재연결 | `rtspsrc` 자동 처리 | 수동 재연결 루프 (2초 sleep) |

**OpenCV N=4 성능 붕괴 원인 (복합)**:
- `cv2.VideoCapture` RTSP 수신 자체가 불안정 (단일 스트림도 제한적)
- 4룸 × 5스레드 = 20개 Python 스레드의 GIL 경합
- `frame.copy() × 4 × 4 = 16회/프레임`의 메모리 복사 누적
- 룸당 ffmpeg 서브프로세스 4개 동시 실행으로 인한 IPC 오버헤드

**GStreamer 안정성의 근거**: 4개 파이프라인이 각각 독립 GLib 스레드(C 레벨)에서 실행되며 GIL이 없고, 버퍼는 참조 카운팅 zero-copy로 전달된다. N이 늘어도 각 파이프라인은 서로 영향을 주지 않는다.

---

## 관찰 사항

### 로컬 Docker 테스트 (WHIP 카메라 입력)

- 4개 branch 모두 목표 FPS 달성 (live/record 30fps, ai/preview 5fps)
- GStreamer `leaky=downstream` 정책으로 AI branch 처리 지연이 live/record에 영향 없음
- WHEP 프리뷰: 송출 전 접속 → "연결 중..." 재시도, 송출 시작 후 자동 연결 (< 2초)
- MediaMTX RTSP(8554) / WHIP·WHEP(8889) / API(9997) 포트 정상 응답

### 향후 개선 항목

1. `rtspsrc`에 `retry-delay` 설정 → 송출 중단 시 자동 재연결
2. AI branch `leaky=downstream` + `drop=true` 이미 적용 → 처리 지연이 파이프라인에 영향 없음
3. WHEP audio transceiver 추가 → 마이크 오디오 실시간 모니터링

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

- **4분기 파이프라인 설계**: live/record/ai/preview를 독립적으로 격리해 각 branch의 policy를 달리 적용한 구조가 실제로 잘 동작했다. 로컬 Docker에서 목표 FPS를 모두 달성한 것이 이를 증명한다.
- **SSE EventBus**: GLib 스레드 ↔ asyncio 간 `run_coroutine_threadsafe` 패턴이 안정적으로 동작했다.
- **WHEP 실시간 프리뷰**: MediaMTX가 WHEP을 내장 지원하므로 별도 SFU 없이 < 100ms 지연을 달성했다.

### 안정화 단계에서 발견·수정된 문제들

Docker로 전체 스택을 통합한 이후, 개별 태스크 단계에서 발견되지 않았던 문제들이 연달아 나타났다.

| 문제 | 원인 | 수정 |
|------|------|------|
| `POST /pipeline/start` 실패 | `_DEFAULT_SOURCE`가 파일 경로로 하드코딩 | 환경변수 `MEDIAMTX_RTSP_URL`로 RTSP URL 주입 |
| AI 얼굴 미감지 | 모델 경로 `.parent` 체인 개수 오류 | `5 → 3` 수정 (Docker 경로 `/app/media/models/`) |
| WHIP 탭 전환 시 연결 끊김 | `PublisherPage` 언마운트로 RTCPeerConnection 소멸 | 항상 마운트 유지, CSS로 탭 전환 처리 |
| CORS 오류 | `localhost:3000` 미허용 | FastAPI CORS origins에 추가 |
| MediaMTX 파싱 오류 | `webrtcICEServers2` 키 버전 불일치 | 로컬 불필요 설정 제거 |
| 모델 볼륨 마운트 충돌 | 이미지 내장 경로와 볼륨 마운트 경로 충돌 | 볼륨 마운트 제거, Dockerfile 빌드 시 내장 |
| HLS 프리뷰 정적 화면 | `React.memo`로 리렌더 차단 후 HLS가 세그먼트 갱신 불가 | **HLS 자체를 WHEP으로 교체** |
| `useCallback` 빌드 오류 | `noUnusedLocals` strict mode에서 import 누락 | `useAIResults.ts`에 `useCallback` import 추가 |

### HLS → WHEP 전환 (T-16 재구현)

HLS 프리뷰의 "정적 화면" 문제는 단순 버그가 아니었다.
근본 원인은 HLS의 구조적 특성(세그먼트 단위 버퍼링)에 있었고,
이를 진짜로 해결하려면 프로토콜 자체를 바꿔야 했다.

**결과**:
- HLS의 2~6초 지연 → WHEP < 100ms (Zoom과 동일한 실시간감)
- `syncedResult` / `latestResultRef` / `handleTimeSync` / `getResultAtTime` 등 시간 동기화 복잡도 전부 제거
- `WhepPlayer` 컴포넌트: 자동 재시도(2초 × 10회) + 수동 재시도 버튼 + 연결 상태 표시
- 파이프라인 중지 → 재시도 → 재시작 후 자동 복구 동작 확인

### 다음 시도해볼 것

1. Prometheus + Grafana로 장기 메트릭 시각화
2. TURN 서버 추가로 NAT 환경에서도 WHIP 송출 보장
3. MediaPipe LIVE_STREAM → batch 처리로 throughput 향상 실험
4. WHEP에 audio transceiver 추가하여 마이크 모니터링
