#!/usr/bin/env python3
# T-07: GStreamer Python GI 바인딩 기본 연동 확인 — Dev Container 전용
# 사전 조건: apt-get install python3-gst-1.0 python3-gi gir1.2-gstreamer-1.0
# 실행: python3 apps/control-api/src/gstreamer_hello.py
import gi

gi.require_version("Gst", "1.0")
from gi.repository import Gst  # noqa: E402

Gst.init(None)
print(f"GStreamer 버전: {Gst.version_string()}")

pipeline = Gst.parse_launch("videotestsrc num-buffers=30 ! fakesink")
pipeline.set_state(Gst.State.PLAYING)

bus = pipeline.get_bus()
msg = bus.timed_pop_filtered(
    Gst.CLOCK_TIME_NONE,
    Gst.MessageType.EOS | Gst.MessageType.ERROR,
)

if msg.type == Gst.MessageType.ERROR:
    err, debug = msg.parse_error()
    print(f"오류: {err}, {debug}")
elif msg.type == Gst.MessageType.EOS:
    print("스트림 종료 (EOS)")

pipeline.set_state(Gst.State.NULL)
print("파이프라인 종료")
