import asyncio
import os
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles

from .event_bus import bus as event_bus
from .pipeline import HLS_DIR, get_status, start_pipelines, stop_pipeline, tracker


async def _metrics_loop():
    while True:
        await event_bus.publish_async(
            {"type": "metrics", "data": tracker.get_snapshot(), "timestamp": time.time()}
        )
        await asyncio.sleep(1)


@asynccontextmanager
async def lifespan(app: FastAPI):
    event_bus.set_loop(asyncio.get_event_loop())
    task = asyncio.create_task(_metrics_loop())
    yield
    task.cancel()


os.makedirs(HLS_DIR, exist_ok=True)

app = FastAPI(title="OpenCV Pipeline API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/pipeline/start")
def start(rooms: str = "room1"):
    room_list = [r.strip() for r in rooms.split(",") if r.strip()]
    return start_pipelines(room_list)


@app.post("/pipeline/stop")
def stop():
    return stop_pipeline()


@app.get("/pipeline/status")
def status():
    return get_status()


@app.get("/metrics")
def metrics():
    return tracker.get_snapshot()


@app.get("/events")
async def events():
    return StreamingResponse(
        event_bus.subscribe(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


app.mount("/hls", StaticFiles(directory=HLS_DIR), name="hls")
