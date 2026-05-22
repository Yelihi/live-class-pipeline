from fastapi import APIRouter

from ..services import pipeline_manager

router = APIRouter(prefix="/pipeline", tags=["pipeline"])


@router.post("/start")
def start(input_path: str = "media/gstreamer/sample.mp4"):
    return pipeline_manager.start_pipeline(input_path)


@router.post("/stop")
def stop():
    return pipeline_manager.stop_pipeline()


@router.get("/status")
def status():
    return pipeline_manager.get_status()
