from fastapi import APIRouter
from sqlalchemy import text

from app.db.session import engine

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
