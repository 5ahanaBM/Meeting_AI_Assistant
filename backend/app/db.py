"""
Async database session management using SQLAlchemy (PostgreSQL + asyncpg).

- Reads DATABASE_URL from settings (must be async URL, e.g. postgresql+asyncpg://...)
- Provides:
    * engine: AsyncEngine
    * SessionLocal: async_sessionmaker[AsyncSession]
    * Base: Declarative base class for ORM models
    * get_db(): FastAPI dependency yielding an AsyncSession
"""

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession, AsyncEngine
from sqlalchemy.orm import DeclarativeBase
from .config import settings

# ---------- Declarative Base ----------
class Base(DeclarativeBase):
    """Base class for ORM models."""
    pass

# ---------- Async Engine ----------
# Expect settings.database_url to be like:
# postgresql+asyncpg://app:app@localhost:5432/meeting_ai
engine: AsyncEngine = create_async_engine(
    settings.database_url,
    echo=False,          # set True to see SQL during development
    pool_pre_ping=True,  # verifies connections are alive
)

# ---------- Async Session Factory ----------
SessionLocal = async_sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
    class_=AsyncSession,
)

# ---------- FastAPI Dependency ----------
async def get_db() -> AsyncSession:
    """
    Yields an AsyncSession per request. Use with: `db: AsyncSession = Depends(get_db)`
    """
    async with SessionLocal() as session:
        yield session

# IMPORTANT:
# Do NOT call Base.metadata.create_all() anywhere.
# Schema changes are managed exclusively by Alembic migrations.