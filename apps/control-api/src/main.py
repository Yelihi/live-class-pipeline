import asyncio
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI

from .routes.events import router as events_router
from .routes.metrics import router as metrics_router
from .routes.pipeline import router as pipeline_router
from .services import glib_loop
from .services.event_bus import bus as event_bus
from .services.metrics_collector import collector as metrics


async def _publish_metrics_loop():
    while True:
        await event_bus.publish_async(
            {"type": "metrics", "data": metrics.get_snapshot(), "timestamp": time.time()}
        )
        await asyncio.sleep(1)


@asynccontextmanager
async def lifespan(app: FastAPI):
    event_bus.set_loop(asyncio.get_event_loop())
    glib_loop.start()
    task = asyncio.create_task(_publish_metrics_loop())
    yield
    task.cancel()
    glib_loop.stop()


app = FastAPI(title="Live Class Pipeline Control API", lifespan=lifespan)
app.include_router(pipeline_router)
app.include_router(metrics_router)
app.include_router(events_router)


@app.get("/health")
def health():
    return {"status": "ok"}
