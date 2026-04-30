from fastapi import Header, HTTPException, status

from app.core.config import settings


async def require_api_key(x_api_key: str | None = Header(default=None)) -> None:
    """Header-based API key gate for mutating endpoints.

    When ADMIN_API_KEY is unset, the gate is open (suitable for local/dev).
    When set, requests must send X-API-Key matching the configured value.
    """
    if not settings.auth_enabled:
        return
    if not x_api_key or x_api_key != settings.admin_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid or missing X-API-Key",
            headers={"WWW-Authenticate": "ApiKey"},
        )
