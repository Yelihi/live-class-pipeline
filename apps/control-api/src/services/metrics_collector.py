import threading
from dataclasses import dataclass

import gi

gi.require_version("Gst", "1.0")
from gi.repository import Gst  # noqa: E402


@dataclass
class BranchMetrics:
    fps: float = 0.0
    last_pts_ns: int = 0
    frame_count: int = 0


class MetricsCollector:
    def __init__(self):
        self._lock = threading.Lock()
        self._rooms: dict[str, dict[str, BranchMetrics]] = {}

    def reset(self):
        with self._lock:
            self._rooms.clear()

    def remove_room(self, room: str):
        with self._lock:
            self._rooms.pop(room, None)

    def attach_probe(self, room: str, pipeline: Gst.Pipeline, branch_name: str, element_name: str):
        element = pipeline.get_by_name(element_name)
        if element is None:
            return
        pad = element.get_static_pad("sink")
        if pad is None:
            return
        pad.add_probe(Gst.PadProbeType.BUFFER, self._make_callback(room, branch_name))

    def _make_callback(self, room: str, branch_name: str):
        def callback(pad, info):
            buf = info.get_buffer()
            with self._lock:
                room_data = self._rooms.setdefault(room, {})
                m = room_data.setdefault(branch_name, BranchMetrics())
                if m.last_pts_ns > 0 and buf.pts > m.last_pts_ns:
                    delta_ns = buf.pts - m.last_pts_ns
                    m.fps = round(1e9 / delta_ns, 1)
                m.last_pts_ns = buf.pts
                m.frame_count += 1
            return Gst.PadProbeReturn.OK

        return callback

    def get_snapshot(self) -> dict:
        with self._lock:
            rooms = {
                room: {
                    branch: {"fps": m.fps, "frame_count": m.frame_count}
                    for branch, m in branches.items()
                }
                for room, branches in self._rooms.items()
            }

        aggregate: dict[str, dict] = {}
        for branch in ["live", "record", "ai", "preview"]:
            fps_list = [rooms[r][branch]["fps"] for r in rooms if branch in rooms[r]]
            frames_list = [rooms[r][branch]["frame_count"] for r in rooms if branch in rooms[r]]
            if fps_list:
                aggregate[branch] = {
                    "avg_fps": round(sum(fps_list) / len(fps_list), 1),
                    "total_frames": sum(frames_list),
                }

        return {"rooms": rooms, "aggregate": aggregate}


# 싱글톤 인스턴스
collector = MetricsCollector()
