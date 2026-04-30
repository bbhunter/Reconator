import re
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.db.models import ModuleStatus, TargetStatus

DOMAIN_REGEX = re.compile(
    r"^(?!-)[A-Za-z0-9-]{1,63}(?<!-)(\.[A-Za-z0-9-]{1,63})+$"
)


def _normalise_domain(v: str) -> str:
    v = v.strip().lower()
    v = re.sub(r"^https?://", "", v)
    v = v.rstrip("/")
    if not DOMAIN_REGEX.match(v):
        raise ValueError(f"invalid domain: {v!r} — provide a bare domain like example.com")
    return v


class TargetCreate(BaseModel):
    url: str = Field(..., min_length=3, max_length=253)
    tags: list[str] = Field(default_factory=list, max_length=20)
    selected_modules: Optional[list[str]] = None
    notes: Optional[str] = Field(default=None, max_length=2000)

    @field_validator("url")
    @classmethod
    def validate_domain(cls, v: str) -> str:
        return _normalise_domain(v)

    @field_validator("tags")
    @classmethod
    def normalise_tags(cls, v: list[str]) -> list[str]:
        cleaned = sorted({t.strip().lower() for t in v if t.strip()})
        for t in cleaned:
            if not re.match(r"^[a-z0-9._-]{1,32}$", t):
                raise ValueError(f"invalid tag: {t!r}")
        return cleaned


class TargetBulkCreate(BaseModel):
    urls: list[str] = Field(..., min_length=1, max_length=500)
    tags: list[str] = Field(default_factory=list, max_length=20)
    selected_modules: Optional[list[str]] = None


class TargetBulkResult(BaseModel):
    created: list[int]
    conflicts: list[str]
    errors: dict[str, str]


class ScanResultRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    module: str
    status: ModuleStatus
    output: Optional[str]
    error: Optional[str]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]


class ScanResultSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    module: str
    status: ModuleStatus
    completed_at: Optional[datetime]
    has_output: bool = False


class TargetRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    url: str
    status: TargetStatus
    error: Optional[str]
    tags: list[str] = []
    selected_modules: Optional[list[str]] = None
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]


class TargetDetail(TargetRead):
    notes: Optional[str] = None
    results: list[ScanResultSummary] = []


class TargetList(BaseModel):
    items: list[TargetRead]
    total: int
    page: int
    page_size: int


class StatsResponse(BaseModel):
    queued: int
    running: int
    completed: int
    failed: int
    cancelled: int
    total: int
    avg_duration_seconds: Optional[float] = None
