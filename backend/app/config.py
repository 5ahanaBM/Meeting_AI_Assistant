"""
Application configuration loader for environment variables.

This module centralizes environment variable access, with validation and
type-safe parsing for predictable configuration behavior across environments.
"""

from pathlib import Path
from typing import List
from pydantic import BaseModel, Field, field_validator
from dotenv import load_dotenv
import os

# Resolve the backend root and load .env explicitly so it works regardless of CWD
BACKEND_ROOT = Path(__file__).resolve().parents[1]
ENV_PATH = BACKEND_ROOT / ".env"
load_dotenv(dotenv_path=ENV_PATH)

class Settings(BaseModel):
    """
    Settings model for application configuration.

    Attributes:
        app_env (str): Application environment (e.g., 'dev', 'prod').
        app_host (str): Host to bind the FastAPI server.
        app_port (int): Port to bind the FastAPI server.
        database_url (str): SQLAlchemy-compatible database URL.
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

    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./local.db")

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

    enable_diarization: bool = os.getenv("ENABLE_DIARIZATION", "false").lower() == "true"
    enable_code_switch_tagging: bool = os.getenv("ENABLE_CODE_SWITCH_TAGGING", "true").lower() == "true"

    @field_validator("cors_allowed_origins", mode="before")
    @classmethod
    def _parse_origins(cls, v: str | List[str]) -> List[str]:
        """
        Parse a comma-separated list of origins from the environment variable.

        Args:
            v (str | List[str]): The raw value or a pre-parsed list.

        Returns:
            List[str]: A list of allowed CORS origins.
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
        """
        Ensure VAD mode is in the accepted range [0, 3].

        Args:
            v (int): The configured VAD mode.

        Returns:
            int: The validated VAD mode.

        Raises:
            ValueError: If the provided VAD mode is out of range.
        """
        if v < 0 or v > 3:
            raise ValueError("VAD_MODE must be between 0 and 3.")
        return v

settings = Settings()
