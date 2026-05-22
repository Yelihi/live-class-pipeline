import logging
import threading

import gi

gi.require_version("Gst", "1.0")
from gi.repository import Gst  # noqa: E402

from .ai_worker import AIWorker
from .event_bus import bus as event_bus
from .metrics_collector import collector as metrics

logger = logging.getLogger(__name__)

Gst.init(None)

_pipeline: Gst.Pipeline | None = None
_ai_worker: AIWorker | None = None
_lock = threading.Lock()

def _source_element(source: str) -> str:
    if source.startswith("rtsp://"):
        return f"rtspsrc location={source} latency=200"
    return f"filesrc location={source}"


# tee + 4 branch: live/record(30fps fakesink), ai(5fps BGR appsink), preview(5fps fakesink)
_PIPELINE_TMPL = """
  {source_element} !
  decodebin !
  videoconvert !
  tee name=t

  t. ! queue name=live_queue  max-size-buffers=0  max-size-time=0  max-size-bytes=0  !
       fakesink name=live_sink  sync=false

  t. ! queue name=record_queue max-size-buffers=0  max-size-time=0  max-size-bytes=0  !
       fakesink name=record_sink sync=false

  t. ! queue name=ai_queue    leaky=downstream max-size-buffers=5 !
       videoscale ! videorate !
       video/x-raw,width=320,height=240,framerate=5/1 !
       videoconvert !
       video/x-raw,format=BGR !
       appsink name=ai_sink emit-signals=true sync=false max-buffers=1 drop=true

  t. ! queue name=preview_queue leaky=downstream max-size-buffers=5 !
       videoscale ! videorate !
       video/x-raw,width=320,height=240,framerate=5/1 !
       videoconvert !
       fakesink name=preview_sink sync=false
"""


def _on_bus_message(bus, message):
    t = message.type
    if t == Gst.MessageType.ERROR:
        err, debug = message.parse_error()
        logger.error("GStreamer 오류: %s (%s)", err, debug)
    elif t == Gst.MessageType.WARNING:
        warn, debug = message.parse_warning()
        logger.warning("GStreamer 경고: %s (%s)", warn, debug)
    elif t == Gst.MessageType.EOS:
        logger.info("GStreamer EOS — 스트림 종료")


def _make_appsink_callback(worker: AIWorker, pipeline: Gst.Pipeline):
    def on_new_sample(appsink) -> Gst.FlowReturn:
        sample = appsink.emit("pull-sample")
        if sample is None:
            return Gst.FlowReturn.ERROR
        return worker.on_frame(sample.get_buffer(), sample.get_caps())

    return on_new_sample


def start_pipeline(input_path: str) -> dict:
    global _pipeline, _ai_worker
    with _lock:
        if _pipeline is not None:
            return {"error": "이미 실행 중"}
        metrics.reset()
        _pipeline = Gst.parse_launch(
            _PIPELINE_TMPL.format(source_element=_source_element(input_path))
        )

        bus = _pipeline.get_bus()
        bus.add_signal_watch()
        bus.connect("message", _on_bus_message)

        for branch, element_name in [
            ("live", "live_sink"),
            ("record", "record_sink"),
            ("preview", "preview_sink"),
        ]:
            metrics.attach_probe(_pipeline, branch, element_name)

        # AI branch: appsink → AIWorker
        _ai_worker = AIWorker(event_bus)
        appsink = _pipeline.get_by_name("ai_sink")
        if appsink:
            appsink.connect("new-sample", _make_appsink_callback(_ai_worker, _pipeline))

        _pipeline.set_state(Gst.State.PLAYING)
    event_bus.publish({"type": "pipeline", "state": "started", "input": input_path})
    return {"state": "started"}


def stop_pipeline() -> dict:
    global _pipeline, _ai_worker
    with _lock:
        if _pipeline is not None:
            _pipeline.set_state(Gst.State.NULL)
            _pipeline = None
        if _ai_worker is not None:
            _ai_worker.close()
            _ai_worker = None
    event_bus.publish({"type": "pipeline", "state": "stopped"})
    return {"state": "stopped"}


def get_status() -> dict:
    if _pipeline is None:
        return {"state": "stopped"}
    _, state, _ = _pipeline.get_state(0)
    return {"state": state.value_nick}
