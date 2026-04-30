from functools import lru_cache
from typing import Optional

from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    app_name: str = "Reconator"
    app_version: str = "2.1.0"
    app_env: str = Field(default="development")
    log_level: str = Field(default="INFO")

    api_prefix: str = "/api/v1"
    cors_origins: str = "*"

    database_url: Optional[str] = None
    postgres_host: str = "db"
    postgres_port: int = 5432
    postgres_db: str = "reconator"
    postgres_user: str = "reconator"
    postgres_password: str = "reconator"

    # Auth — when admin_api_key is unset, mutations are open (dev mode).
    admin_api_key: Optional[str] = None

    # Rate limiting (writes only)
    rate_limit_writes: str = "20/minute"
    rate_limit_bulk: str = "5/minute"

    # Notifications
    telegram_api_key: Optional[str] = None
    telegram_chat_id: Optional[str] = None
    webhook_url: Optional[str] = None
    webhook_kind: str = "generic"  # generic | slack | discord

    # Observability
    sentry_dsn: Optional[str] = None
    metrics_enabled: bool = True

    # Worker
    worker_poll_interval_seconds: int = 30
    module_timeout_seconds: int = 1800
    max_concurrent_scans: int = 1
    modules_dir: str = "/app/modules"
    results_dir: str = "/app/results"

    # Static frontend
    serve_static_web: bool = False
    static_web_dir: str = "/app/static_web"

    # DB pool
    db_pool_size: int = 5
    db_max_overflow: int = 10

    @computed_field  # type: ignore[misc]
    @property
    def sqlalchemy_url(self) -> str:
        if self.database_url:
            url = self.database_url
            if url.startswith("postgres://"):
                url = url.replace("postgres://", "postgresql+psycopg://", 1)
            elif url.startswith("postgresql://") and "+psycopg" not in url:
                url = url.replace("postgresql://", "postgresql+psycopg://", 1)
            return url
        return (
            f"postgresql+psycopg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def auth_enabled(self) -> bool:
        return bool(self.admin_api_key)


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
