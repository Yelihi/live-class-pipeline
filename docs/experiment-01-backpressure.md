# 실험 01: GStreamer tee 백프레셔 — leaky vs non-leaky queue

**관련 태스크**: T-04 (Issue #7)  
**실험 스크립트**: `media/gstreamer/pipelines/03-backpressure-experiment.sh`  
**실행 환경**: macOS, GStreamer 1.28.2 (Homebrew)

---

## 실험 목적

`tee`를 통해 여러 branch로 분기할 때, 느린 branch(AI inference 시뮬레이션)가 빠른 branch(live)에 미치는 영향을 확인하고 `queue leaky` 정책으로 해결한다.

---

## 실험 1: non-leaky queue — 백프레셔 발생

### 파이프라인 구조

```
videotestsrc (10 frames) ! tee name=t
  t. ! queue (non-leaky) ! identity              ! live_sink
  t. ! queue (non-leaky) ! identity sleep=500ms  ! ai_sink
```

### 실행 명령

```bash
bash media/gstreamer/pipelines/03-backpressure-experiment.sh no-leaky
```

### 관찰 결과

- PREROLLING 단계에서 `live_sink`, `ai_sink` 두 branch 모두 caps 협상 완료
- tee는 두 branch 모두 현재 버퍼를 소비할 때까지 **다음 프레임 전송을 차단**
- AI branch가 1 프레임당 500ms 소요 → live branch도 500ms/frame으로 강제 동기화
- 10 프레임 처리 예상 총 소요 시간: **약 5초** (10 × 0.5s)

### 결론

`leaky=no`(기본값) queue에서는 tee가 **가장 느린 branch 속도에 전체 파이프라인을 맞춘다**.  
AI inference처럼 느린 consumer가 live branch까지 블락하는 백프레셔 문제가 발생한다.

---

## 실험 2: leaky=downstream queue — 백프레셔 해소

### 파이프라인 구조

```
videotestsrc (10 frames) ! tee name=t
  t. ! queue name=live_q                                  ! identity ! live_sink
  t. ! queue name=ai_q leaky=downstream max-size-buffers=3 ! identity sleep=500ms ! ai_sink
```

### 실행 명령

```bash
bash media/gstreamer/pipelines/03-backpressure-experiment.sh leaky
```

### 관찰 결과

- PREROLLING 단계에서 `live_sink`, `ai_sink`, `ai_identity` 모두 caps 협상 완료
- ai_q가 가득 차면(max 3 buffers) **가장 오래된 버퍼를 자동으로 drop** → tee는 즉시 다음 프레임으로 진행
- live branch는 tee의 블락 없이 30fps 속도 유지
- ai branch는 queue에서 최대 3개 버퍼만 처리 (나머지는 drop)

### 결론

`leaky=downstream`은 버퍼가 가득 찼을 때 **오래된 버퍼를 버리고 최신 프레임을 유지**한다.  
AI처럼 "최신 프레임만 처리하면 되는" branch에 적합하며, live branch 속도에 영향을 주지 않는다.

---

## 실험 비교 요약

| 항목 | 실험 1 (non-leaky) | 실험 2 (leaky=downstream) |
|------|-------------------|--------------------------|
| live branch 속도 | AI와 동기화(500ms/frame) | 30fps 유지 |
| AI branch 처리 | 10 프레임 전부 | 최대 3 프레임 (나머지 drop) |
| 데이터 유실 | 없음 | AI branch에서 발생 |
| 총 소요 시간 | ~5초 | ~1.5초 |
| 적합한 용도 | 녹화(유실 불가) | AI, preview(최신 프레임 우선) |

---

## T-04 최종 queue 정책 결정

`media/gstreamer/pipelines/04-four-branch-with-policy.sh`에 반영한 정책:

| Branch | Queue 정책 | 이유 |
|--------|-----------|------|
| live | `max-size-buffers=0 max-size-time=0 max-size-bytes=0` (무제한, non-leaky) | 화면 출력은 끊김 없이 |
| record | `max-size-buffers=0 max-size-time=0 max-size-bytes=0` (무제한, non-leaky) | 녹화 파일 유실 불가 |
| ai | `leaky=downstream max-size-buffers=5` | inference는 최신 프레임만 필요 |
| preview | `leaky=downstream max-size-buffers=5` | 운영자 preview는 최신 상태 우선 |

---

## 참고 자료

- [GStreamer queue element 문서](https://gstreamer.freedesktop.org/documentation/coreelements/queue.html) — `leaky`, `max-size-buffers` 파라미터
- [GStreamer 스케줄링 모델](https://gstreamer.freedesktop.org/documentation/application-development/advanced/threads.html) — "When are threads used?" 섹션
- [identity element 문서](https://gstreamer.freedesktop.org/documentation/coreelements/identity.html) — `sleep-time` 파라미터
