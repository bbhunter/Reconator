from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import db_session
from app.db.models import Target, TargetStatus
from app.schemas.target import (
    StatsResponse,
    TargetCreate,
    TargetDetail,
    TargetList,
    TargetRead,
)

router = APIRouter(prefix="/targets", tags=["targets"])


@router.post("", response_model=TargetRead, status_code=status.HTTP_201_CREATED)
def create_target(
    payload: TargetCreate, db: Session = Depends(db_session)
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
    target = Target(url=payload.url, status=TargetStatus.queued)
    db.add(target)
    db.commit()
    db.refresh(target)
    return TargetRead.model_validate(target)


@router.get("", response_model=TargetList)
def list_targets(
    db: Session = Depends(db_session),
    status_filter: Optional[TargetStatus] = Query(None, alias="status"),
    search: Optional[str] = None,
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

    total = db.scalar(count_stmt) or 0
    items = db.scalars(stmt.offset((page - 1) * page_size).limit(page_size)).all()
    return TargetList(
        items=[TargetRead.model_validate(t) for t in items],
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
    return StatsResponse(
        queued=counts.get("queued", 0),
        running=counts.get("running", 0),
        completed=counts.get("completed", 0),
        failed=counts.get("failed", 0),
        total=sum(counts.values()),
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


@router.delete("/{target_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_target(target_id: int, db: Session = Depends(db_session)) -> None:
    target = db.get(Target, target_id)
    if target is None:
        raise HTTPException(status_code=404, detail="target not found")
    if target.status == TargetStatus.running:
        target.status = TargetStatus.cancelled
        db.commit()
        return
    db.delete(target)
    db.commit()
