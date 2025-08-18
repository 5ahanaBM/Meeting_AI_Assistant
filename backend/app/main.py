"""
FastAPI application entry point.

- Wires routers
- Uses async DB (managed via dependencies inside routers)
- Schema is managed by Alembic; no create_all() here
"""

from fastapi import FastAPI
from .config import settings
from . import models  # keep if your routers import models indirectly
from .routers.health import router as health_router
from .ws.ingest import router as ws_router


def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application.
    """
    app = FastAPI(
        title="Meeting Assistant API",
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # Routers
    app.include_router(health_router)
    app.include_router(ws_router)

    return app


# IMPORTANT: Alembic owns schema migrations now.
# Do NOT call Base.metadata.create_all(bind=engine).

app = create_app()