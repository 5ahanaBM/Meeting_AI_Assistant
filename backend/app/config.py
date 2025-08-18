"""
Application configuration loader for environment variables.

Centralizes environment variable access with validation and type-safe parsing.
Adds both async (app) and sync (alembic) DB URLs for a clean Postgres setup.
"""

from __future__ import annotations

from pathlib import Path
from typing import List
from pydantic import BaseModel, Field, field_validator
from dotenv import load_dotenv
import os

# Resolve the backend root and load .env explicitly so it works regardless of CWD
BACKEND_ROOT = Path(__file__).resolve().parents[1]
ENV_PATH = BACKEND_ROOT / ".env"
load_dotenv(dotenv_path=ENV_PATH)

def _env_bool(name: str, default: bool) -> bool:
    val = os.getenv(name)
    if val is None:
        return default
    return val.strip().lower() in {"1", "true", "yes", "y", "on"}

def _ensure_asyncpg(url: str) -> str:
    """
    Ensure the URL uses the async driver for SQLAlchemy if it's PostgreSQL.
    If it's already async or a non-Postgres URL (e.g., sqlite), leave it as-is.
    """
    if url.startswith("postgresql+asyncpg://"):
        return url
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+asyncpg://", 1)
    return url

def _ensure_sync_psycopg(url: str) -> str:
    """
    Ensure the URL uses the sync driver for Alembic if it's PostgreSQL.
    Alembic prefers sync URLs (postgresql://).
    """
    if url.startswith("postgresql://"):
        return url
    if url.startswith("postgresql+asyncpg://"):
        return url.replace("postgresql+asyncpg://", "postgresql://", 1)
    return url

class Settings(BaseModel):
    """
    Settings model for application configuration.

    Attributes:
        app_env (str): Application environment (e.g., 'dev', 'prod').
        app_host (str): Host to bind the FastAPI server.
        app_port (int): Port to bind the FastAPI server.

        database_url (str): Async SQLAlchemy URL for the app (e.g., postgresql+asyncpg://...).
        alembic_database_url (str): Sync SQLAlchemy URL for Alembic (e.g., postgresql://...).

        ollama_host (str): Base URL for the local Ollama server.
        llm_model (str): Model name served by Ollama for QA/summarization.

        asr_model (str): faster-whisper model identifier.
        asr_device (str): Device to run ASR on ('cuda' or 'cpu').
        asr_compute_type (str): Precision mode for CTranslate2 (e.g., 'float16').

        vad_mode (int): VAD aggressiveness from 0 (least) to 3 (most).

        embedding_model (str): Sentence-transformers model for retrieval embeddings.
        faiss_index (str): FAISS index type identifier (e.g., 'FlatIP').
        qa_top_k (int): Number of chunks to retrieve for QA.

        cors_allowed_origins (List[str]): Allowed origins for CORS.
        log_level (str): Logging verbosity (e.g., 'INFO', 'DEBUG').

        enable_diarization (bool): Feature flag for speaker diarization.
        enable_code_switch_tagging (bool): Feature flag to tag per-utterance language.
    """
    app_env: str = os.getenv("APP_ENV", "dev")
    app_host: str = os.getenv("APP_HOST", "127.0.0.1")
    app_port: int = int(os.getenv("APP_PORT", "8000"))

    # App URL (async for runtime)
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./local.db")

    # Alembic URL (sync for migrations)
    alembic_database_url: str = os.getenv("ALEMBIC_DATABASE_URL", "")

    ollama_host: str = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434")
    llm_model: str = os.getenv("LLM_MODEL", "llama3.1:8b-instruct-q4_K_M")

    asr_model: str = os.getenv("ASR_MODEL", "large-v3")
    asr_device: str = os.getenv("ASR_DEVICE", "cuda")
    asr_compute_type: str = os.getenv("ASR_COMPUTE_TYPE", "float16")

    vad_mode: int = int(os.getenv("VAD_MODE", "2"))

    embedding_model: str = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
    faiss_index: str = os.getenv("FAISS_INDEX", "FlatIP")
    qa_top_k: int = int(os.getenv("QA_TOP_K", "8"))

    cors_allowed_origins: List[str] = Field(default_factory=list)
    log_level: str = os.getenv("LOG_LEVEL", "INFO")

    enable_diarization: bool = _env_bool("ENABLE_DIARIZATION", False)
    enable_code_switch_tagging: bool = _env_bool("ENABLE_CODE_SWITCH_TAGGING", True)

    @field_validator("cors_allowed_origins", mode="before")
    @classmethod
    def _parse_origins(cls, v: str | List[str]) -> List[str]:
        """
        Parse a comma-separated list of origins from the environment variable.
        """
        if isinstance(v, list):
            return v
        raw = os.getenv("CORS_ALLOWED_ORIGINS", "").strip()
        if not raw:
            return []
        return [item.strip() for item in raw.split(",") if item.strip()]

    @field_validator("vad_mode")
    @classmethod
    def _validate_vad_mode(cls, v: int) -> int:
        """Ensure VAD mode is in the accepted range [0, 3]."""
        if v < 0 or v > 3:
            raise ValueError("VAD_MODE must be between 0 and 3.")
        return v

    @field_validator("database_url")
    @classmethod
    def _normalize_app_db_url(cls, v: str) -> str:
        """
        Ensure runtime DB URL uses async driver for Postgres.
        Leaves SQLite and other schemes untouched.
        """
        return _ensure_asyncpg(v)

    @field_validator("alembic_database_url")
    @classmethod
    def _normalize_alembic_db_url(cls, v: str) -> str:
        """
        Ensure Alembic DB URL uses sync driver for Postgres.
        If not provided, derive from database_url.
        """
        if not v:
            # derive from the async database_url if possible
            base = os.getenv("DATABASE_URL", "sqlite:///./local.db")
            return _ensure_sync_psycopg(base)
        return _ensure_sync_psycopg(v)

settings = Settings()