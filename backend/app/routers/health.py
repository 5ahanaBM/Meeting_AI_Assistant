"""
Healthcheck endpoint for service monitoring.

Provides a simple readiness probe for orchestration and local testing.
"""

from fastapi import APIRouter

router = APIRouter(prefix="/health", tags=["health"])

@router.get("/ready")
def ready() -> dict:
    """
    Readiness probe endpoint.

    Returns:
        dict: A payload indicating service status.
    """
    return {"status": "ok"}
