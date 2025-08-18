"""
Healthcheck endpoint for service monitoring.

- /health/ready: verifies API is up and DB is reachable.
"""

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from app.db import get_db

router = APIRouter(prefix="/health", tags=["health"])

@router.get("/ready")
async def ready(db: AsyncSession = Depends(get_db)) -> dict:
    """
    Readiness probe that pings the database.
    """
    await db.execute(text("SELECT 1"))
    return {"status": "ok"}