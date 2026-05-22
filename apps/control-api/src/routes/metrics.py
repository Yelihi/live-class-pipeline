from fastapi import APIRouter

from ..services.metrics_collector import collector as metrics

router = APIRouter(tags=["metrics"])


@router.get("/metrics")
def get_metrics():
    return metrics.get_snapshot()
