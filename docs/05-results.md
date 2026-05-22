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
