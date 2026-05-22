import threading
from dataclasses import dataclass, field

import gi

gi.require_version("Gst", "1.0")
from gi.repository import Gst  # noqa: E402


@dataclass
class BranchMetrics:
    fps: float = 0.0
    dropped_frames: int = 0
    last_pts_ns: int = 0
    frame_count: int = 0


class MetricsCollector:
    def __init__(self):
        self._lock = threading.Lock()
        self.branches: dict[str, BranchMetrics] = {
            "live": BranchMetrics(),
            "record": BranchMetrics(),
            "ai": BranchMetrics(),
            "preview": BranchMetrics(),
        }

    def reset(self):
        with self._lock:
            for m in self.branches.values():
                m.fps = 0.0
                m.dropped_frames = 0
                m.last_pts_ns = 0
                m.frame_count = 0

    def attach_probe(self, pipeline: Gst.Pipeline, branch_name: str, element_name: str):
        element = pipeline.get_by_name(element_name)
        if element is None:
            return
        pad = element.get_static_pad("sink")
        if pad is None:
            return
        pad.add_probe(Gst.PadProbeType.BUFFER, self._make_callback(branch_name))

    def _make_callback(self, branch_name: str):
        def callback(pad, info):
            buf = info.get_buffer()
            with self._lock:
                m = self.branches[branch_name]
                if m.last_pts_ns > 0 and buf.pts > m.last_pts_ns:
                    delta_ns = buf.pts - m.last_pts_ns
                    m.fps = round(1e9 / delta_ns, 1)
                m.last_pts_ns = buf.pts
                m.frame_count += 1
            return Gst.PadProbeReturn.OK

        return callback

    def get_snapshot(self) -> dict:
        with self._lock:
            return {
                name: {
                    "fps": m.fps,
                    "frame_count": m.frame_count,
                    "dropped_frames": m.dropped_frames,
                }
                for name, m in self.branches.items()
            }


# 싱글톤 인스턴스
collector = MetricsCollector()
