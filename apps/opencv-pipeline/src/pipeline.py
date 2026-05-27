import glob
import logging
import os
import queue
import subprocess
import threading
import time
from pathlib import Path

import cv2
import mediapipe as mp
from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python import vision

from .attention_analyzer import analyze
from .event_bus import bus as event_bus

logger = logging.getLogger(__name__)

HLS_DIR = os.environ.get("HLS_DIR", "/tmp/hls")
OUTPUT_DIR = os.environ.get("OUTPUT_DIR", "/app/output")
RTSP_BASE = os.environ.get("MEDIAMTX_RTSP_BASE_URL", "rtsp://mediamtx:8554")
MODEL_PATH = Path(
    os.environ.get(
        "FACE_LANDMARKER_MODEL",
        "/app/media/models/face_landmarker.task",
    )
)

AI_INTERVAL = 0.2  # 5fps

_STOP = object()  # 큐 종료 sentinel


# ---------------------------------------------------------------------------
# 큐 유틸리티
# ---------------------------------------------------------------------------

def _put_leaky(q: queue.Queue, item) -> None:
    """GStreamer leaky=downstream 동일 semantics — 가득 차면 오래된 항목 제거"""
    while q.full():
        try:
            q.get_nowait()
        except queue.Empty:
            break
    try:
        q.put_nowait(item)
    except queue.Full:
        pass


def _inject_sentinel(q: queue.Queue) -> None:
    """_STOP을 큐에 강제 삽입 — 가득 찬 경우 항목 하나를 제거하고 삽입"""
    try:
        q.put_nowait(_STOP)
    except queue.Full:
        try:
            q.get_nowait()
        except queue.Empty:
            pass
        try:
            q.put_nowait(_STOP)
        except queue.Full:
            pass


# ---------------------------------------------------------------------------
# MetricsTracker — GStreamer metrics_collector.get_snapshot()과 동일 응답 포맷
# ---------------------------------------------------------------------------

class MetricsTracker:
    def __init__(self):
        self._lock = threading.Lock()
        self._data: dict = {}

    def reset(self):
        with self._lock:
            self._data.clear()

    def remove_room(self, room: str):
        with self._lock:
            self._data.pop(room, None)

    def record(self, room: str, branch: str):
        now = time.monotonic()
        with self._lock:
            rb = (
                self._data.setdefault(room, {})
                .setdefault(branch, {"fps": 0.0, "frame_count": 0, "last_ts": 0.0})
            )
            if rb["last_ts"] > 0:
                delta = now - rb["last_ts"]
                if delta > 0:
                    rb["fps"] = round(1.0 / delta, 1)
            rb["last_ts"] = now
            rb["frame_count"] += 1

    def get_snapshot(self) -> dict:
        with self._lock:
            rooms = {
                room: {
                    branch: {"fps": v["fps"], "frame_count": v["frame_count"]}
                    for branch, v in branches.items()
                }
                for room, branches in self._data.items()
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


tracker = MetricsTracker()


# ---------------------------------------------------------------------------
# 베이스 스레드
# ---------------------------------------------------------------------------

class BaseWorkerThread(threading.Thread):
    def __init__(self, room: str, **kwargs):
        super().__init__(daemon=True, **kwargs)
        self._room = room

    def run(self):
        try:
            self._work()
        except Exception:
            logger.exception("[%s] 스레드 %s 오류", self._room, self.name)

    def _work(self):
        raise NotImplementedError


# ---------------------------------------------------------------------------
# CaptureThread — RTSP 읽기 + 4개 큐에 프레임 분배
# ---------------------------------------------------------------------------

class CaptureThread(BaseWorkerThread):
    def __init__(self, room: str, rtsp_url: str, rp: "RoomPipeline"):
        super().__init__(room=room, name=f"capture-{room}")
        self._rtsp_url = rtsp_url
        self._rp = rp

    def _work(self):
        while not self._rp.stopped.is_set():
            cap = cv2.VideoCapture(self._rtsp_url)
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            if not cap.isOpened():
                logger.warning("[%s] RTSP 연결 실패, 2초 후 재시도", self._room)
                time.sleep(2)
                continue

            logger.info("[%s] RTSP 연결 성공: %s", self._room, self._rtsp_url)
            last_ai_ts = 0.0

            while not self._rp.stopped.is_set():
                ret, frame = cap.read()
                if not ret:
                    logger.warning("[%s] 프레임 읽기 실패 — 재연결", self._room)
                    break
                now = time.monotonic()
                # live / record: 모든 프레임
                self._rp.live_q.put(frame.copy())
                self._rp.record_q.put(frame.copy())
                # ai / preview: 5fps 샘플링 (leaky)
                if now - last_ai_ts >= AI_INTERVAL:
                    last_ai_ts = now
                    _put_leaky(self._rp.ai_q, frame.copy())
                    _put_leaky(self._rp.preview_q, frame.copy())

            cap.release()
            if not self._rp.stopped.is_set():
                time.sleep(2)

        # 종료 시 모든 큐에 sentinel 주입
        for q in [self._rp.live_q, self._rp.record_q, self._rp.ai_q, self._rp.preview_q]:
            _inject_sentinel(q)
        logger.info("[%s] CaptureThread 종료", self._room)


# ---------------------------------------------------------------------------
# LiveThread — ffmpeg subprocess HLS 출력
# ---------------------------------------------------------------------------

class LiveThread(BaseWorkerThread):
    def __init__(self, room: str, q: queue.Queue):
        super().__init__(room=room, name=f"live-{room}")
        self._q = q
        self._proc: subprocess.Popen | None = None

    def _spawn(self, w: int, h: int):
        room_hls = f"{HLS_DIR}/{self._room}"
        os.makedirs(room_hls, exist_ok=True)
        for f in glob.glob(f"{room_hls}/*.ts"):
            os.remove(f)
        self._proc = subprocess.Popen(
            [
                "ffmpeg", "-y",
                "-f", "rawvideo", "-pix_fmt", "bgr24",
                "-s", f"{w}x{h}", "-r", "30",
                "-i", "pipe:0",
                "-c:v", "libx264", "-tune", "zerolatency",
                "-preset", "ultrafast", "-b:v", "2000k",
                "-f", "hls", "-hls_time", "2", "-hls_list_size", "10",
                "-hls_segment_filename", f"{room_hls}/seg%05d.ts",
                f"{room_hls}/stream.m3u8",
            ],
            stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        logger.info("[%s] ffmpeg HLS 프로세스 시작 (PID %d)", self._room, self._proc.pid)

    def _teardown(self):
        if self._proc and self._proc.poll() is None:
            self._proc.stdin.close()
            try:
                self._proc.wait(timeout=3)
            except subprocess.TimeoutExpired:
                self._proc.kill()
                self._proc.wait()

    def _work(self):
        w = h = None
        while True:
            item = self._q.get()
            if item is _STOP:
                break
            if w is None:
                h, w = item.shape[:2]
                self._spawn(w, h)
            if self._proc is None or self._proc.poll() is not None:
                self._spawn(w, h)
            try:
                self._proc.stdin.write(item.tobytes())
            except BrokenPipeError:
                logger.warning("[%s] LiveThread BrokenPipeError — ffmpeg 재시작", self._room)
                self._spawn(w, h)
            tracker.record(self._room, "live")
        self._teardown()
        logger.info("[%s] LiveThread 종료", self._room)


# ---------------------------------------------------------------------------
# RecordThread — ffmpeg subprocess MKV 출력
# ---------------------------------------------------------------------------

class RecordThread(BaseWorkerThread):
    def __init__(self, room: str, q: queue.Queue):
        super().__init__(room=room, name=f"record-{room}")
        self._q = q
        self._proc: subprocess.Popen | None = None

    def _spawn(self, w: int, h: int):
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        output_path = f"{OUTPUT_DIR}/{self._room}_recording.mkv"
        self._proc = subprocess.Popen(
            [
                "ffmpeg", "-y",
                "-f", "rawvideo", "-pix_fmt", "bgr24",
                "-s", f"{w}x{h}", "-r", "30",
                "-i", "pipe:0",
                "-c:v", "libx264", "-preset", "ultrafast",
                output_path,
            ],
            stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        logger.info("[%s] ffmpeg MKV 프로세스 시작 → %s", self._room, output_path)

    def _teardown(self):
        if self._proc and self._proc.poll() is None:
            self._proc.stdin.close()
            try:
                self._proc.wait(timeout=3)
            except subprocess.TimeoutExpired:
                self._proc.kill()
                self._proc.wait()

    def _work(self):
        w = h = None
        while True:
            item = self._q.get()
            if item is _STOP:
                break
            if w is None:
                h, w = item.shape[:2]
                self._spawn(w, h)
            if self._proc is None or self._proc.poll() is not None:
                self._spawn(w, h)
            try:
                self._proc.stdin.write(item.tobytes())
            except BrokenPipeError:
                logger.warning("[%s] RecordThread BrokenPipeError — ffmpeg 재시작", self._room)
                self._spawn(w, h)
            tracker.record(self._room, "record")
        self._teardown()
        logger.info("[%s] RecordThread 종료", self._room)


# ---------------------------------------------------------------------------
# AIThread — MediaPipe FaceLandmarker LIVE_STREAM
# ---------------------------------------------------------------------------

class AIThread(BaseWorkerThread):
    def __init__(self, room: str, q: queue.Queue):
        super().__init__(room=room, name=f"ai-{room}")
        self._q = q
        self._lock = threading.Lock()
        self._pending_pts_ns: int = 0
        self._pending_wall_ms: int = 0
        self._detector: vision.FaceLandmarker | None = None

    def _create_detector(self) -> vision.FaceLandmarker:
        options = vision.FaceLandmarkerOptions(
            base_options=mp_python.BaseOptions(model_asset_path=str(MODEL_PATH)),
            running_mode=vision.RunningMode.LIVE_STREAM,
            num_faces=1,
            min_face_detection_confidence=0.5,
            result_callback=self._on_result,
        )
        return vision.FaceLandmarker.create_from_options(options)

    def _on_result(self, result, _output_image, _timestamp_ms: int) -> None:
        with self._lock:
            pts_ns = self._pending_pts_ns
            wall_ms = self._pending_wall_ms

        attention = analyze(result.face_landmarks)
        event_bus.publish(
            {
                "type": "ai_result",
                "pts_ns": pts_ns,
                "wall_clock_ms": wall_ms,
                "face_detected": attention.face_detected,
                "left_ear": attention.left_ear,
                "right_ear": attention.right_ear,
                "avg_ear": attention.avg_ear,
                "is_facing_front": attention.is_facing_front,
                "attention_score": attention.attention_score,
            }
        )

    def _work(self):
        self._detector = self._create_detector()
        ts_ms = 0  # 단조 증가 타임스탬프 (MediaPipe 요구사항)

        while True:
            item = self._q.get()
            if item is _STOP:
                break
            frame_rgb = cv2.cvtColor(item, cv2.COLOR_BGR2RGB)
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame_rgb)
            ts_ms += 200  # 5fps = 200ms 간격
            with self._lock:
                self._pending_pts_ns = time.monotonic_ns()
                self._pending_wall_ms = time.time_ns() // 1_000_000
            self._detector.detect_async(mp_image, ts_ms)
            tracker.record(self._room, "ai")

        if self._detector:
            self._detector.close()
        logger.info("[%s] AIThread 종료", self._room)


# ---------------------------------------------------------------------------
# PreviewThread — 프레임 카운트만 (GStreamer fakesink 동일)
# ---------------------------------------------------------------------------

class PreviewThread(BaseWorkerThread):
    def __init__(self, room: str, q: queue.Queue):
        super().__init__(room=room, name=f"preview-{room}")
        self._q = q

    def _work(self):
        while True:
            item = self._q.get()
            if item is _STOP:
                break
            tracker.record(self._room, "preview")
        logger.info("[%s] PreviewThread 종료", self._room)


# ---------------------------------------------------------------------------
# RoomPipeline — 단일 룸 스레드 그룹
# ---------------------------------------------------------------------------

class RoomPipeline:
    def __init__(self, room: str, rtsp_url: str):
        self.stopped = threading.Event()
        self.live_q: queue.Queue = queue.Queue(maxsize=0)
        self.record_q: queue.Queue = queue.Queue(maxsize=0)
        self.ai_q: queue.Queue = queue.Queue(maxsize=5)
        self.preview_q: queue.Queue = queue.Queue(maxsize=5)

        self._threads = [
            CaptureThread(room, rtsp_url, self),
            LiveThread(room, self.live_q),
            RecordThread(room, self.record_q),
            AIThread(room, self.ai_q),
            PreviewThread(room, self.preview_q),
        ]

    def start(self):
        for t in self._threads:
            t.start()

    def stop(self):
        self.stopped.set()
        # sentinel 주입 — 각 worker 스레드 unblock
        for q in [self.live_q, self.record_q, self.ai_q, self.preview_q]:
            _inject_sentinel(q)
        for t in self._threads:
            t.join(timeout=5)


# ---------------------------------------------------------------------------
# OpenCVPipelineManager — 공개 인터페이스 (GStreamer pipeline_manager 동일)
# ---------------------------------------------------------------------------

_rooms: dict[str, RoomPipeline] = {}
_lock = threading.Lock()


def start_pipelines(rooms: list[str]) -> dict:
    global _rooms
    with _lock:
        if _rooms:
            return {"error": "이미 실행 중"}
        tracker.reset()
        for room in rooms:
            rtsp_url = f"{RTSP_BASE}/{room}"
            rp = RoomPipeline(room, rtsp_url)
            rp.start()
            _rooms[room] = rp
            logger.info("[%s] 파이프라인 시작: %s", room, rtsp_url)

    event_bus.publish({"type": "pipeline", "state": "started", "rooms": rooms})
    return {"state": "started", "rooms": rooms}


def stop_pipeline() -> dict:
    global _rooms
    with _lock:
        for rp in _rooms.values():
            rp.stop()
        stopped_rooms = list(_rooms.keys())
        _rooms.clear()

    for room in stopped_rooms:
        tracker.remove_room(room)

    event_bus.publish({"type": "pipeline", "state": "stopped"})
    return {"state": "stopped"}


def get_status() -> dict:
    if not _rooms:
        return {"state": "stopped"}
    return {"state": "running", "room_count": len(_rooms)}
