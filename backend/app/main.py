"""
FastAPI application entry point.

This module wires routers, initializes the database metadata,
and exposes an ASGI app for local development.
"""

from fastapi import FastAPI
from .config import settings
from .db import Base, engine
# IMPORTANT: import models so the Table metadata is registered
from . import models  # noqa: F401
from .routers.health import router as health_router
from .ws.ingest import router as ws_router


def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application.

    Returns:
        FastAPI: Configured FastAPI instance with routes registered.
    """
    app = FastAPI(title="Meeting Assistant API", version="0.1.0", docs_url="/docs", redoc_url="/redoc")

    # Include routers
    app.include_router(health_router)
    app.include_router(ws_router)

    return app


# Create DB schema if not present — AFTER models import above.
Base.metadata.create_all(bind=engine)

app = create_app()