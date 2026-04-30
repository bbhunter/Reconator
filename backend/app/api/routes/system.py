from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.core.auth import require_api_key
from app.core.config import settings
from app.services.notifier import notifier as live_notifier

router = APIRouter(prefix="/system", tags=["system"])


class SystemInfo(BaseModel):
    name: str
    version: str
    env: str
    auth_required: bool
    notifications: dict[str, bool]


@router.get("/info", response_model=SystemInfo)
def system_info() -> SystemInfo:
    return SystemInfo(
        name=settings.app_name,
        version=settings.app_version,
        env=settings.app_env,
        auth_required=settings.auth_enabled,
        notifications={
            "telegram": bool(settings.telegram_api_key and settings.telegram_chat_id),
            "webhook": bool(settings.webhook_url),
        },
    )


class TestNotifyResponse(BaseModel):
    sent: bool
    enabled: bool


@router.post(
    "/test-notify",
    response_model=TestNotifyResponse,
    dependencies=[Depends(require_api_key)],
)
def test_notify() -> TestNotifyResponse:
    if not live_notifier.enabled:
        return TestNotifyResponse(sent=False, enabled=False)
    live_notifier.send("Reconator: test notification ✅")
    return TestNotifyResponse(sent=True, enabled=True)
