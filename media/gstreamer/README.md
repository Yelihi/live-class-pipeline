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

`pipelines/` 안의 파일은 `t{번호}_{설명}.sh` 형식으로 저장한다.

```
pipelines/
  t02_basic_pipeline.sh       # T-02: 기본 파이프라인
  t03_encode_h264.sh          # T-03: H.264 인코딩
  t04_tee_leaky_queue.sh      # T-04: tee + leaky queue 실험
  t05_record_mkv.sh           # T-05: MKV 녹화
  t06_hls_output.sh           # T-06: HLS 출력
```

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
