import csv
import io
import json
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import Response, StreamingResponse
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import db_session
from app.core.auth import require_api_key
from app.core.config import settings
from app.core.limiter import limiter
from app.db.models import Target, TargetStatus
from app.schemas.target import (
    StatsResponse,
    TargetBulkCreate,
    TargetBulkResult,
    TargetCreate,
    TargetDetail,
    TargetList,
    TargetRead,
)
from app.schemas.target import _normalise_domain  # noqa: PLC2701

router = APIRouter(prefix="/targets", tags=["targets"])


@router.post(
    "",
    response_model=TargetRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_api_key)],
)
@limiter.limit(settings.rate_limit_writes)
def create_target(
    request: Request,
    payload: TargetCreate,
    db: Session = Depends(db_session),
) -> TargetRead:
    existing = db.scalar(
        select(Target).where(
            Target.url == payload.url,
            Target.status.in_([TargetStatus.queued, TargetStatus.running]),
        )
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"target already {existing.status.value} (id={existing.id})",
        )
    target = Target(
        url=payload.url,
        status=TargetStatus.queued,
        tags=payload.tags,
        selected_modules=payload.selected_modules,
        notes=payload.notes,
    )
    db.add(target)
    db.commit()
    db.refresh(target)
    return TargetRead.model_validate(target)


@router.post(
    "/bulk",
    response_model=TargetBulkResult,
    dependencies=[Depends(require_api_key)],
)
@limiter.limit(settings.rate_limit_bulk)
def bulk_create(
    request: Request,
    payload: TargetBulkCreate,
    db: Session = Depends(db_session),
) -> TargetBulkResult:
    created: list[int] = []
    conflicts: list[str] = []
    errors: dict[str, str] = {}

    for raw in payload.urls:
        try:
            url = _normalise_domain(raw)
        except ValueError as exc:
            errors[raw] = str(exc)
            continue
        existing = db.scalar(
            select(Target).where(
                Target.url == url,
                Target.status.in_([TargetStatus.queued, TargetStatus.running]),
            )
        )
        if existing:
            conflicts.append(url)
            continue
        target = Target(
            url=url,
            status=TargetStatus.queued,
            tags=sorted({t.lower() for t in payload.tags}),
            selected_modules=payload.selected_modules,
        )
        db.add(target)
        db.flush()
        created.append(target.id)
    db.commit()
    return TargetBulkResult(created=created, conflicts=conflicts, errors=errors)


@router.get("", response_model=TargetList)
def list_targets(
    db: Session = Depends(db_session),
    status_filter: Optional[TargetStatus] = Query(None, alias="status"),
    search: Optional[str] = None,
    tag: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
) -> TargetList:
    stmt = select(Target).order_by(Target.created_at.desc())
    count_stmt = select(func.count()).select_from(Target)

    if status_filter:
        stmt = stmt.where(Target.status == status_filter)
        count_stmt = count_stmt.where(Target.status == status_filter)
    if search:
        like = f"%{search.lower()}%"
        stmt = stmt.where(func.lower(Target.url).like(like))
        count_stmt = count_stmt.where(func.lower(Target.url).like(like))

    rows = db.scalars(stmt.offset((page - 1) * page_size).limit(page_size * 2)).all()
    if tag:
        wanted = tag.lower()
        rows = [t for t in rows if wanted in (t.tags or [])][:page_size]
    else:
        rows = rows[:page_size]

    total = db.scalar(count_stmt) or 0
    return TargetList(
        items=[TargetRead.model_validate(t) for t in rows],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/stats", response_model=StatsResponse)
def stats(db: Session = Depends(db_session)) -> StatsResponse:
    rows = db.execute(
        select(Target.status, func.count()).group_by(Target.status)
    ).all()
    counts = {s.value: 0 for s in TargetStatus}
    for s, c in rows:
        counts[s.value if hasattr(s, "value") else s] = c

    avg_seconds: Optional[float] = None
    durations = db.execute(
        select(Target.started_at, Target.completed_at).where(
            Target.status == TargetStatus.completed,
            Target.started_at.isnot(None),
            Target.completed_at.isnot(None),
        )
    ).all()
    if durations:
        total_seconds = sum(
            (c - s).total_seconds() for s, c in durations if s and c
        )
        avg_seconds = round(total_seconds / len(durations), 2)

    return StatsResponse(
        queued=counts.get("queued", 0),
        running=counts.get("running", 0),
        completed=counts.get("completed", 0),
        failed=counts.get("failed", 0),
        cancelled=counts.get("cancelled", 0),
        total=sum(counts.values()),
        avg_duration_seconds=avg_seconds,
    )


@router.get("/export")
def export_targets(
    db: Session = Depends(db_session),
    format: str = Query("csv", pattern="^(csv|json)$"),
    status_filter: Optional[TargetStatus] = Query(None, alias="status"),
) -> Response:
    stmt = select(Target).order_by(Target.created_at.desc())
    if status_filter:
        stmt = stmt.where(Target.status == status_filter)
    rows = db.scalars(stmt).all()

    if format == "json":
        payload = [
            {
                "id": t.id,
                "url": t.url,
                "status": t.status.value,
                "tags": t.tags or [],
                "created_at": t.created_at.isoformat() if t.created_at else None,
                "completed_at": t.completed_at.isoformat() if t.completed_at else None,
                "error": t.error,
            }
            for t in rows
        ]
        return Response(
            content=json.dumps(payload, indent=2),
            media_type="application/json",
            headers={"Content-Disposition": 'attachment; filename="targets.json"'},
        )

    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["id", "url", "status", "tags", "created_at", "completed_at", "error"])
    for t in rows:
        writer.writerow(
            [
                t.id,
                t.url,
                t.status.value,
                "|".join(t.tags or []),
                t.created_at.isoformat() if t.created_at else "",
                t.completed_at.isoformat() if t.completed_at else "",
                (t.error or "").replace("\n", " "),
            ]
        )
    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="targets.csv"'},
    )


@router.get("/{target_id}", response_model=TargetDetail)
def get_target(target_id: int, db: Session = Depends(db_session)) -> TargetDetail:
    target = db.get(Target, target_id)
    if target is None:
        raise HTTPException(status_code=404, detail="target not found")
    detail = TargetDetail.model_validate(target)
    detail.results = [
        {
            "module": r.module,
            "status": r.status,
            "completed_at": r.completed_at,
            "has_output": bool(r.output),
        }
        for r in target.results
    ]
    return detail


@router.delete(
    "/{target_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_api_key)],
)
def delete_target(target_id: int, db: Session = Depends(db_session)) -> None:
    target = db.get(Target, target_id)
    if target is None:
        raise HTTPException(status_code=404, detail="target not found")
    if target.status == TargetStatus.running:
        target.cancel_requested = True
        db.commit()
        return
    db.delete(target)
    db.commit()


@router.post(
    "/{target_id}/cancel",
    response_model=TargetRead,
    dependencies=[Depends(require_api_key)],
)
def cancel_target(target_id: int, db: Session = Depends(db_session)) -> TargetRead:
    target = db.get(Target, target_id)
    if target is None:
        raise HTTPException(status_code=404, detail="target not found")
    if target.status == TargetStatus.running:
        target.cancel_requested = True
    elif target.status == TargetStatus.queued:
        target.status = TargetStatus.cancelled
        target.completed_at = target.completed_at
    else:
        raise HTTPException(
            status_code=409,
            detail=f"cannot cancel a {target.status.value} target",
        )
    db.commit()
    db.refresh(target)
    return TargetRead.model_validate(target)


@router.post(
    "/{target_id}/rescan",
    response_model=TargetRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_api_key)],
)
def rescan_target(target_id: int, db: Session = Depends(db_session)) -> TargetRead:
    src = db.get(Target, target_id)
    if src is None:
        raise HTTPException(status_code=404, detail="target not found")
    new = Target(
        url=src.url,
        status=TargetStatus.queued,
        tags=list(src.tags or []),
        selected_modules=list(src.selected_modules) if src.selected_modules else None,
        notes=src.notes,
    )
    db.add(new)
    db.commit()
    db.refresh(new)
    return TargetRead.model_validate(new)
