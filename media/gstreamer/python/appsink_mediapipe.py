#!/usr/bin/env python3
# T-17/T-18: appsink → MediaPipe LIVE_STREAM 연동 + EAR/attention score
# Dev Container(Ubuntu 22.04) 전용 — gi(python3-gst-1.0) 필요
# 실행: python3 media/gstreamer/python/appsink_mediapipe.py [input.mp4]
import sys
import threading
from pathlib import Path

import gi

gi.require_version("Gst", "1.0")
from gi.repository import Gst, GLib  # noqa: E402

import numpy as np  # noqa: E402
import mediapipe as mp  # noqa: E402
from mediapipe.tasks import python  # noqa: E402
from mediapipe.tasks.python import vision  # noqa: E402
from attention_analyzer import analyze  # noqa: E402

Gst.init(None)

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
MODEL_PATH = PROJECT_ROOT / "media" / "models" / "face_landmarker.task"
DEFAULT_INPUT = PROJECT_ROOT / "media" / "gstreamer" / "sample.mp4"

# GST_CLOCK_TIME_NONE: 타임스탬프 미설정 상태
GST_CLOCK_TIME_NONE = 2**64 - 1

# ── MediaPipe 초기화 (LIVE_STREAM 모드) ──────────────────────────────────
_latest: dict = {"landmarks": None, "ts_ms": 0}
_lock = threading.Lock()


def _on_result(result, _output_image, timestamp_ms: int) -> None:
    with _lock:
        _latest["landmarks"] = result.face_landmarks
        _latest["ts_ms"] = timestamp_ms
    att = analyze(result.face_landmarks)
    if att.face_detected:
        print(
            f"[{timestamp_ms:8d}ms] "
            f"EAR={att.avg_ear:.3f}  "
            f"front={att.is_facing_front}  "
            f"score={att.attention_score:.3f}"
        )
    else:
        print(f"[{timestamp_ms:8d}ms] 얼굴 없음")


base_options = python.BaseOptions(model_asset_path=str(MODEL_PATH))
options = vision.FaceLandmarkerOptions(
    base_options=base_options,
    running_mode=vision.RunningMode.LIVE_STREAM,
    num_faces=1,
    min_face_detection_confidence=0.5,
    result_callback=_on_result,
)
detector = vision.FaceLandmarker.create_from_options(options)


# ── appsink 콜백 ─────────────────────────────────────────────────────────
def on_new_sample(appsink) -> Gst.FlowReturn:
    sample = appsink.emit("pull-sample")
    if sample is None:
        return Gst.FlowReturn.ERROR

    buf = sample.get_buffer()
    caps = sample.get_caps()
    structure = caps.get_structure(0)
    width = structure.get_value("width")
    height = structure.get_value("height")

    # PTS 미설정 프레임 건너뜀 (LIVE_STREAM 타임스탬프 단조 증가 요구)
    if buf.pts == GST_CLOCK_TIME_NONE:
        return Gst.FlowReturn.OK

    success, map_info = buf.map(Gst.MapFlags.READ)
    if not success:
        return Gst.FlowReturn.ERROR

    try:
        frame_bgr = np.frombuffer(map_info.data, dtype=np.uint8).reshape((height, width, 3))
        frame_rgb = frame_bgr[:, :, ::-1].copy()  # BGR → RGB (MediaPipe SRGB 요구)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame_rgb)
        timestamp_ms = int(buf.pts / 1_000_000)  # ns → ms
        detector.detect_async(mp_image, timestamp_ms)
    finally:
        buf.unmap(map_info)

    return Gst.FlowReturn.OK


# ── GStreamer 파이프라인 ───────────────────────────────────────────────────
input_path = sys.argv[1] if len(sys.argv) > 1 else str(DEFAULT_INPUT)
print(f"==> 입력: {input_path}")
print(f"==> AI branch: 320×240 5fps BGR → MediaPipe LIVE_STREAM")
print("==> Ctrl+C 로 종료")
print()

pipeline = Gst.parse_launch(f"""
    filesrc location={input_path} !
    decodebin !
    videoconvert !
    videoscale !
    videorate !
    video/x-raw,width=320,height=240,framerate=5/1 !
    videoconvert !
    video/x-raw,format=BGR !
    appsink name=ai_sink emit-signals=true sync=false max-buffers=1 drop=true
""")

appsink = pipeline.get_by_name("ai_sink")
appsink.connect("new-sample", on_new_sample)

loop = GLib.MainLoop()


def on_message(bus, message):
    t = message.type
    if t == Gst.MessageType.EOS:
        print("\n==> EOS — 파이프라인 종료")
        loop.quit()
    elif t == Gst.MessageType.ERROR:
        err, debug = message.parse_error()
        print(f"\n==> 오류: {err} ({debug})")
        loop.quit()


bus = pipeline.get_bus()
bus.add_signal_watch()
bus.connect("message", on_message)

pipeline.set_state(Gst.State.PLAYING)

try:
    loop.run()
except KeyboardInterrupt:
    print("\nCtrl+C — 파이프라인 종료")
finally:
    pipeline.set_state(Gst.State.NULL)
    detector.close()
