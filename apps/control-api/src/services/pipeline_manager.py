import logging
import os
import threading

import gi

gi.require_version("Gst", "1.0")
from gi.repository import Gst  # noqa: E402

from .ai_worker import AIWorker
from .event_bus import bus as event_bus
from .metrics_collector import collector as metrics

logger = logging.getLogger(__name__)

Gst.init(None)

_pipelines: dict[str, Gst.Pipeline] = {}
_ai_workers: dict[str, AIWorker] = {}
_lock = threading.Lock()

HLS_DIR = os.environ.get("HLS_DIR", "/tmp/hls")
RTSP_BASE = os.environ.get("MEDIAMTX_RTSP_BASE_URL", "rtsp://mediamtx:8554")


def _source_element(source: str) -> str:
    if source.startswith("rtsp://"):
        return f"rtspsrc location={source} latency=200"
    return f"filesrc location={source}"


_PIPELINE_TMPL = """
  {{source_element}} !
  decodebin !
  videoconvert !
  tee name=t

  t. ! queue name=live_queue  max-size-buffers=0  max-size-time=0  max-size-bytes=0  !
       identity name=live_sink silent=true !
       videoconvert !
       video/x-raw,format=I420 !
       x264enc tune=zerolatency bitrate=2000 speed-preset=ultrafast !
       hlssink2 location={hls_dir}/seg%05d.ts playlist-location={hls_dir}/stream.m3u8
                target-duration=2 max-files=10

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


def _make_appsink_callback(worker: AIWorker):
    def on_new_sample(appsink) -> Gst.FlowReturn:
        try:
            sample = appsink.emit("pull-sample")
            if sample is None:
                return Gst.FlowReturn.OK
            return worker.on_frame(sample.get_buffer(), sample.get_caps())
        except Exception:
            logger.exception("appsink new-sample 처리 오류")
            return Gst.FlowReturn.OK

    return on_new_sample


def _start_one(room: str, input_path: str) -> None:
    """단일 룸 파이프라인을 시작한다. _lock 내부에서 호출해야 한다."""
    room_hls_dir = f"{HLS_DIR}/{room}"
    os.makedirs(room_hls_dir, exist_ok=True)

    pipeline_str = _PIPELINE_TMPL.format(hls_dir=room_hls_dir).replace(
        "{source_element}", _source_element(input_path)
    )
    pipeline = Gst.parse_launch(pipeline_str)

    gst_bus = pipeline.get_bus()
    gst_bus.add_signal_watch()
    gst_bus.connect("message", _on_bus_message)

    for branch, element_name in [
        ("live", "live_sink"),
        ("record", "record_sink"),
        ("ai", "ai_sink"),
        ("preview", "preview_sink"),
    ]:
        metrics.attach_probe(room, pipeline, branch, element_name)

    worker = AIWorker(event_bus)
    appsink = pipeline.get_by_name("ai_sink")
    if appsink:
        appsink.connect("new-sample", _make_appsink_callback(worker))
    else:
        logger.error("[%s] ai_sink 엘리먼트를 찾을 수 없습니다", room)

    pipeline.set_state(Gst.State.PLAYING)
    _pipelines[room] = pipeline
    _ai_workers[room] = worker
    logger.info("[%s] 파이프라인 시작: %s", room, input_path)


def start_pipelines(rooms: list[str]) -> dict:
    global _pipelines, _ai_workers
    with _lock:
        if _pipelines:
            return {"error": "이미 실행 중"}
        metrics.reset()
        for room in rooms:
            rtsp_url = f"{RTSP_BASE}/{room}"
            _start_one(room, rtsp_url)
    event_bus.publish({"type": "pipeline", "state": "started", "rooms": rooms})
    return {"state": "started", "rooms": rooms}


def stop_pipeline() -> dict:
    global _pipelines, _ai_workers
    with _lock:
        for pipeline in _pipelines.values():
            pipeline.set_state(Gst.State.NULL)
        _pipelines.clear()
        for worker in _ai_workers.values():
            worker.close()
        _ai_workers.clear()
    event_bus.publish({"type": "pipeline", "state": "stopped"})
    return {"state": "stopped"}


def get_status() -> dict:
    if not _pipelines:
        return {"state": "stopped"}
    _, state, _ = next(iter(_pipelines.values())).get_state(0)
    return {"state": state.value_nick, "room_count": len(_pipelines)}
