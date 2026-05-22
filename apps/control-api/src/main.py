from contextlib import asynccontextmanager

from fastapi import FastAPI

from .routes.metrics import router as metrics_router
from .routes.pipeline import router as pipeline_router
from .services import glib_loop


@asynccontextmanager
async def lifespan(app: FastAPI):
    glib_loop.start()
    yield
    glib_loop.stop()


app = FastAPI(title="Live Class Pipeline Control API", lifespan=lifespan)
app.include_router(pipeline_router)
app.include_router(metrics_router)


@app.get("/health")
def health():
    return {"status": "ok"}
