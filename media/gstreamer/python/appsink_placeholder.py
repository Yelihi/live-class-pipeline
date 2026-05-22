#!/usr/bin/env python3
# T-06: appsink placeholder — Dev Container(Ubuntu 22.04) 전용
# 필요 패키지: python3-gst-1.0 (apt), python3-gi
# 실행: python3 media/gstreamer/python/appsink_placeholder.py [input.mp4]
import sys
import gi

gi.require_version("Gst", "1.0")
from gi.repository import Gst, GLib  # noqa: E402

Gst.init(None)

INPUT = sys.argv[1] if len(sys.argv) > 1 else "media/gstreamer/sample.mp4"

PIPELINE_STR = f"""
  filesrc location={INPUT} !
  decodebin !
  videoconvert !
  videoscale !
  videorate !
  video/x-raw,width=320,height=240,framerate=5/1 !
  videoconvert !
  video/x-raw,format=BGR !
  appsink name=ai_sink emit-signals=true sync=false max-buffers=1 drop=true
"""

pipeline = Gst.parse_launch(PIPELINE_STR)
appsink = pipeline.get_by_name("ai_sink")
loop = GLib.MainLoop()


def on_new_sample(sink):
    sample = sink.emit("pull-sample")
    buf = sample.get_buffer()
    print(f"프레임 수신: PTS={buf.pts / 1e9:.2f}s, 크기={buf.get_size()} bytes")
    return Gst.FlowReturn.OK


appsink.connect("new-sample", on_new_sample)


def on_message(bus, message):
    t = message.type
    if t == Gst.MessageType.EOS:
        print("EOS — 파이프라인 종료")
        loop.quit()
    elif t == Gst.MessageType.ERROR:
        err, debug = message.parse_error()
        print(f"오류: {err} ({debug})")
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
