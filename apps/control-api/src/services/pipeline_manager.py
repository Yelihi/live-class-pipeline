import threading

import gi

gi.require_version("Gst", "1.0")
from gi.repository import Gst  # noqa: E402

Gst.init(None)

_pipeline: Gst.Pipeline | None = None
_lock = threading.Lock()


def start_pipeline(input_path: str) -> dict:
    global _pipeline
    with _lock:
        if _pipeline is not None:
            return {"error": "이미 실행 중"}
        _pipeline = Gst.parse_launch(
            f"filesrc location={input_path} ! decodebin ! videoconvert ! fakesink sync=false"
        )
        _pipeline.set_state(Gst.State.PLAYING)
    return {"state": "started"}


def stop_pipeline() -> dict:
    global _pipeline
    with _lock:
        if _pipeline is not None:
            _pipeline.set_state(Gst.State.NULL)
            _pipeline = None
    return {"state": "stopped"}


def get_status() -> dict:
    if _pipeline is None:
        return {"state": "stopped"}
    _, state, _ = _pipeline.get_state(0)
    return {"state": state.value_nick}
