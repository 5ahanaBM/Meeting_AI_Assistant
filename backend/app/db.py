"""
Database session management using SQLAlchemy.

This module provides a SQLAlchemy engine and a session factory
configured from environment settings.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from .config import settings

# Engine uses the DATABASE_URL from .env
# engine = create_engine(settings.database_url, pool_pre_ping=True)
# For SQLite, disable same-thread check for FastAPI dev reloader.
sqlite_connect_args = {}
if settings.database_url.startswith("sqlite"):
    sqlite_connect_args = {"check_same_thread": False}

engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    connect_args=sqlite_connect_args
)

# Session factory for transactional operations
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for ORM models
Base = declarative_base()

def get_db():
    """
    Yield a database session for request-scoped usage.

    Yields:
        sqlalchemy.orm.Session: A SQLAlchemy session which must be closed by the caller.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
