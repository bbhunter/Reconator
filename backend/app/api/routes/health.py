from fastapi import APIRouter
from sqlalchemy import text

from app.core.metrics import metrics_response, queue_depth
from app.db.models import Target, TargetStatus
from app.db.session import SessionLocal, engine

router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/ready")
def ready() -> dict[str, str]:
    try:
        with engine.connect() as conn:
            conn.execute(text("select 1"))
        return {"status": "ready"}
    except Exception as exc:  # noqa: BLE001
        return {"status": "degraded", "error": str(exc)}


@router.get("/metrics", include_in_schema=False)
def metrics():
    try:
        with SessionLocal() as db:
            depth = (
                db.query(Target).filter(Target.status == TargetStatus.queued).count()
            )
            queue_depth.set(depth)
    except Exception:  # noqa: BLE001
        pass
    return metrics_response()
