from fastapi import APIRouter

from ..services import pipeline_manager

router = APIRouter(prefix="/pipeline", tags=["pipeline"])


@router.post("/start")
def start(rooms: str = "room1"):
    room_list = [r.strip() for r in rooms.split(",") if r.strip()]
    return pipeline_manager.start_pipelines(room_list)


@router.post("/stop")
def stop():
    return pipeline_manager.stop_pipeline()


@router.get("/status")
def status():
    return pipeline_manager.get_status()
