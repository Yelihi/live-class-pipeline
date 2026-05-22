import os
import threading
import time
from pathlib import Path

import gi

gi.require_version("Gst", "1.0")
from gi.repository import Gst  # noqa: E402

import numpy as np  # noqa: E402
import mediapipe as mp  # noqa: E402
from mediapipe.tasks import python  # noqa: E402
from mediapipe.tasks.python import vision  # noqa: E402

from .attention_analyzer import analyze
from .event_bus import EventBus

GST_CLOCK_TIME_NONE = 2**64 - 1
MODEL_PATH = Path(
    os.environ.get(
        "FACE_LANDMARKER_MODEL",
        str(Path(__file__).parent.parent.parent / "media" / "models" / "face_landmarker.task"),
    )
)


class AIWorker:
    def __init__(self, event_bus: EventBus) -> None:
        self._event_bus = event_bus
        self._lock = threading.Lock()
        self._pending_wall_clock_ms: int = 0
        self._pending_pts_ns: int = 0
        self._detector = self._create_detector()

    def _create_detector(self) -> vision.FaceLandmarker:
        options = vision.FaceLandmarkerOptions(
            base_options=python.BaseOptions(model_asset_path=str(MODEL_PATH)),
            running_mode=vision.RunningMode.LIVE_STREAM,
            num_faces=1,
            min_face_detection_confidence=0.5,
            result_callback=self._on_result,
        )
        return vision.FaceLandmarker.create_from_options(options)

    def _on_result(self, result, _output_image, _timestamp_ms: int) -> None:
        with self._lock:
            pts_ns = self._pending_pts_ns
            wall_clock_ms = self._pending_wall_clock_ms

        attention = analyze(result.face_landmarks)
        self._event_bus.publish(
            {
                "type": "ai_result",
                "pts_ns": pts_ns,
                "wall_clock_ms": wall_clock_ms,
                "face_detected": attention.face_detected,
                "left_ear": attention.left_ear,
                "right_ear": attention.right_ear,
                "avg_ear": attention.avg_ear,
                "is_facing_front": attention.is_facing_front,
                "attention_score": attention.attention_score,
            }
        )

    def on_frame(self, buf: Gst.Buffer, caps: Gst.Caps) -> Gst.FlowReturn:
        if buf.pts == GST_CLOCK_TIME_NONE:
            return Gst.FlowReturn.OK

        wall_clock_ms = time.time_ns() // 1_000_000

        success, map_info = buf.map(Gst.MapFlags.READ)
        if not success:
            return Gst.FlowReturn.ERROR

        try:
            structure = caps.get_structure(0)
            w = structure.get_value("width")
            h = structure.get_value("height")
            frame_bgr = np.frombuffer(map_info.data, dtype=np.uint8).reshape((h, w, 3))
            frame_rgb = frame_bgr[:, :, ::-1].copy()
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame_rgb)
            timestamp_ms = int(buf.pts / 1_000_000)

            with self._lock:
                self._pending_wall_clock_ms = wall_clock_ms
                self._pending_pts_ns = buf.pts

            self._detector.detect_async(mp_image, timestamp_ms)
        finally:
            buf.unmap(map_info)

        return Gst.FlowReturn.OK

    def close(self) -> None:
        self._detector.close()
