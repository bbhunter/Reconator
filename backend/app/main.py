from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.routes import health, modules, results, targets
from app.core.config import settings
from app.core.logging import configure_logging
from app.db.base import Base
from app.db.session import engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    with engine.begin() as conn:
        conn.execute(text("select 1"))
        Base.metadata.create_all(bind=conn)
    yield


app = FastAPI(
    title=settings.app_name,
    version="2.0.0",
    description="Automated reconnaissance framework — REST API",
    lifespan=lifespan,
)

origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix=settings.api_prefix)
app.include_router(targets.router, prefix=settings.api_prefix)
app.include_router(results.router, prefix=settings.api_prefix)
app.include_router(modules.router, prefix=settings.api_prefix)


_static_root = Path(settings.static_web_dir)
_index_file = _static_root / "index.html"
_serve_static = settings.serve_static_web and _index_file.exists()

if _serve_static:
    app.mount(
        "/assets",
        StaticFiles(directory=_static_root / "assets"),
        name="assets",
    )

    @app.get("/", include_in_schema=False)
    def index() -> FileResponse:
        return FileResponse(_index_file)

    @app.exception_handler(StarletteHTTPException)
    async def spa_fallback(request, exc: StarletteHTTPException):
        if (
            exc.status_code == 404
            and request.method == "GET"
            and not request.url.path.startswith(("/api", "/docs", "/openapi", "/redoc"))
        ):
            return FileResponse(_index_file)
        return JSONResponse({"detail": exc.detail}, status_code=exc.status_code)
else:

    @app.get("/", include_in_schema=False)
    def root() -> dict[str, str]:
        return {
            "name": settings.app_name,
            "version": "2.0.0",
            "docs": "/docs",
            "api": settings.api_prefix,
        }
