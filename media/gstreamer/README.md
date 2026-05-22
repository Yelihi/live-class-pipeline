# GStreamer 파이프라인 가이드

이 디렉토리에는 GStreamer 파이프라인 실험 스크립트와 Python 제어 코드가 들어간다.

---

## 개발 환경 설정

### Mac 사용자 (권장: Dev Container)

`apt-get`은 Mac에서 동작하지 않는다.  
VS Code에서 Dev Container로 Ubuntu 22.04 환경에 접속해 실행한다.

1. VS Code 확장 설치: **Dev Containers** (`ms-vscode-remote.remote-containers`)
2. VS Code에서 프로젝트 폴더 열기
3. 명령 팔레트 (`Cmd+Shift+P`) → `Dev Containers: Reopen in Container`
4. 컨테이너 빌드 완료 후 GStreamer 자동 설치됨

### Ubuntu 22.04 VM / 서버

```bash
# 프로젝트 루트에서 실행 (sudo 권한 필요)
sudo bash scripts/install-gstreamer.sh

# 또는 전체 개발 환경 한 번에 설정
sudo bash scripts/dev-setup.sh
```

설치되는 GStreamer 버전: Ubuntu 22.04 기본 저장소 기준 **1.20.x**

---

## 설치 확인 명령어

```bash
# 버전 확인
gst-launch-1.0 --version

# 사용 가능한 element 목록 조회
gst-inspect-1.0 --print-all | head -30

# 특정 element 상세 정보 (T-04에서 쓸 tee 미리 확인)
gst-inspect-1.0 tee
gst-inspect-1.0 queue

# Hello World: 테스트 영상 30프레임 생성 후 종료
gst-launch-1.0 videotestsrc num-buffers=30 ! fakesink

# caps 확인 (영상 포맷 정보 출력)
gst-launch-1.0 videotestsrc num-buffers=1 ! videoconvert ! video/x-raw,format=BGR ! fakesink -v
```

---

## GStreamer 핵심 개념

GStreamer는 **element를 `!`로 연결해 파이프라인을 만든다**.  
React에서 컴포넌트를 조합해 UI를 만드는 것과 같은 구조다.

```
[videotestsrc] ! [videoconvert] ! [fakesink]
  영상 생성        색상 변환       출력 버림
```

### 핵심 element

| Element | 역할 |
|---------|------|
| `videotestsrc` | 테스트용 가짜 영상 생성 |
| `filesrc` | 파일에서 데이터 읽기 |
| `rtspsrc` | RTSP 스트림 수신 (T-06에서 사용) |
| `decodebin` | 미디어 자동 디코딩 |
| `videoconvert` | 영상 색상 포맷 변환 |
| `tee` | 스트림을 여러 개로 복사 (T-04에서 사용) |
| `queue` | element 간 버퍼 (T-04에서 leaky 정책 실험) |
| `x264enc` | H.264 인코딩 (T-03에서 사용) |
| `hlssink2` | HLS 세그먼트 출력 (T-06에서 사용) |
| `matroskamux` | MKV 컨테이너 (T-05에서 사용) |
| `appsink` | Python에서 프레임 수신 (T-07에서 사용) |
| `fakesink` | 데이터를 받아 버림 (테스트용) |
| `autovideosink` | 화면에 출력 (GUI 환경 필요) |

### 핵심 개념

| 개념 | 설명 |
|------|------|
| **Pad** | element 간 연결 지점 (입력 sink pad / 출력 src pad) |
| **Caps** | pad가 처리하는 데이터 포맷 (해상도, 색상공간 등) |
| **Bus** | 파이프라인에서 발생하는 이벤트 채널 (error, EOS 등) |
| **State** | NULL → READY → PAUSED → PLAYING |

---

## 파이프라인 스크립트 파일명 컨벤션

`pipelines/` 안의 파일은 `{번호}-{설명}.sh` 형식으로 저장한다.

```
pipelines/
  01-single-branch.sh         # T-02: 파일 입력 → fakesink (단일 브랜치)
  02-encode-h264.sh           # T-03: H.264 인코딩
  03-tee-leaky-queue.sh       # T-04: tee + leaky queue 실험
  04-record-mkv.sh            # T-05: MKV 녹화
  05-hls-output.sh            # T-06: HLS 출력
```

---

## 파이프라인 실행 방법

모든 스크립트는 **프로젝트 루트에서** 실행한다.

### T-02: 단일 브랜치 파이프라인

```bash
# 기본 실행 (sample.mp4 없으면 자동 생성)
bash media/gstreamer/pipelines/01-single-branch.sh

# 다른 파일 지정
bash media/gstreamer/pipelines/01-single-branch.sh /path/to/video.mp4
```

**파이프라인 구조**:
```
[filesrc] → [decodebin] → [videoconvert] → [fakesink]
  파일 읽기    자동 디코딩    색상 변환       출력 버림(서버용)
```

- `-v` 옵션으로 각 pad의 caps(해상도·포맷·FPS) 협상 과정이 출력됨
- GUI 환경에서 화면 출력이 필요하면 스크립트 내 `autovideosink` 주석 해제
- `Ctrl+C`로 종료

### T-03: tee 기반 4분기 파이프라인

```bash
# 기본 실행 (sample.mp4 없으면 자동 생성)
bash media/gstreamer/pipelines/02-four-branch.sh

# 다른 파일 지정
bash media/gstreamer/pipelines/02-four-branch.sh /path/to/video.mp4
```

**파이프라인 구조**:
```
                           ┌─ live_queue    → live_sink    (화면 출력용)
[filesrc] → [decodebin] → [videoconvert] → [tee] ┼─ record_queue → record_sink (파일 저장용)
                                                  ├─ ai_queue     → ai_sink     (AI 분석용)
                                                  └─ preview_queue → preview_sink (운영자 preview)
```

- 각 branch에 `queue`를 반드시 붙여야 tee가 동기화 없이 각 branch를 독립적으로 실행함
- `name=live_sink` 등으로 이름을 붙이면 나중에 Python에서 `pipeline.get_by_name("live_sink")`로 조회 가능
- 실행 로그에서 `live_sink`, `record_sink`, `ai_sink`, `preview_sink`가 모두 출력되면 4분기 성공

### T-04: queue 백프레셔 정책 실험

```bash
# 실험 1: non-leaky — AI 지연이 live branch를 블락하는 현상 관찰
bash media/gstreamer/pipelines/03-backpressure-experiment.sh no-leaky

# 실험 2: leaky — live branch는 정상 속도 유지 확인
bash media/gstreamer/pipelines/03-backpressure-experiment.sh leaky

# 정책 적용된 4분기 파이프라인 실행
bash media/gstreamer/pipelines/04-four-branch-with-policy.sh
```

**queue 정책 요약**:

| Branch | 정책 | 이유 |
|--------|------|------|
| live, record | non-leaky, 무제한 버퍼 | 데이터 유실 불가 |
| ai, preview | `leaky=downstream max-size-buffers=5` | 최신 프레임만 필요 |

- 실험 상세 결과: `docs/experiment-01-backpressure.md` 참고

---

## Python GI 바인딩 확인 (T-07 준비)

GStreamer Python 바인딩은 `pip install`로 설치할 수 없다.  
반드시 `python3-gst-1.0` 시스템 패키지를 통해 설치해야 한다.

```python
# Python에서 GStreamer 임포트 확인
python3 -c "
import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst
Gst.init(None)
print('GStreamer Python 바인딩 OK:', Gst.version_string())
"
```

`--system-site-packages`로 venv를 생성해야 위 임포트가 venv 안에서도 동작한다:

```bash
python3 -m venv .venv --system-site-packages
source .venv/bin/activate
python3 -c "import gi; gi.require_version('Gst','1.0'); from gi.repository import Gst; Gst.init(None); print(Gst.version_string())"
```
