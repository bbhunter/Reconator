import re
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.db.models import ModuleStatus, TargetStatus

DOMAIN_REGEX = re.compile(
    r"^(?!-)[A-Za-z0-9-]{1,63}(?<!-)(\.[A-Za-z0-9-]{1,63})+$"
)


class TargetCreate(BaseModel):
    url: str = Field(..., min_length=3, max_length=253)

    @field_validator("url")
    @classmethod
    def validate_domain(cls, v: str) -> str:
        v = v.strip().lower()
        v = re.sub(r"^https?://", "", v)
        v = v.rstrip("/")
        if not DOMAIN_REGEX.match(v):
            raise ValueError("invalid domain — provide a bare domain like example.com")
        return v


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
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]


class TargetDetail(TargetRead):
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
    total: int
