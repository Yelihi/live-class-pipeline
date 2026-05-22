import os

from fastapi import APIRouter

from ..services import pipeline_manager

router = APIRouter(prefix="/pipeline", tags=["pipeline"])

_DEFAULT_SOURCE = os.environ.get("MEDIAMTX_RTSP_URL", "rtsp://mediamtx:8554/room1")


@router.post("/start")
def start(input_path: str = _DEFAULT_SOURCE):
    return pipeline_manager.start_pipeline(input_path)


@router.post("/stop")
def stop():
    return pipeline_manager.stop_pipeline()


@router.get("/status")
def status():
    return pipeline_manager.get_status()
