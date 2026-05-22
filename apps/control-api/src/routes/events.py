from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from ..services.event_bus import bus

router = APIRouter(tags=["events"])


@router.get("/events")
async def stream_events():
    return StreamingResponse(
        bus.subscribe(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
