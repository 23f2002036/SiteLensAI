"""
SiteLens AI — Centralized Configuration

Loads all settings from .env using pydantic-settings.
"""

from __future__ import annotations

import os
from enum import Enum
from functools import lru_cache
from pathlib import Path
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class VLMBackend(str, Enum):
    OLLAMA = "ollama"
    GROK = "grok"
    GROQ = "groq"
    TRANSFORMERS = "transformers"


class VectorBackend(str, Enum):
    SUPABASE = "supabase"
    FAISS = "faiss"


# ---------------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------------

class Settings(BaseSettings):
    """Application settings loaded from environment / .env file."""

    model_config = SettingsConfigDict(
        env_file=str(Path(__file__).resolve().parent.parent / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # -- VLM --
    vlm_backend: VLMBackend = VLMBackend.GROK
    ollama_host: str = "http://localhost:11434"
    ollama_model: str = "qwen2.5vl"
    grok_api_key: Optional[str] = None
    grok_model: str = "grok-2-vision-latest"
    groq_api_key: Optional[str] = None
    groq_model: str = "qwen/qwen3.6-27b"

    # -- Vector Store --
    vector_backend: VectorBackend = VectorBackend.FAISS
    faiss_index_path: str = "data/faiss_index"
    supabase_url: Optional[str] = None
    supabase_service_key: Optional[str] = None

    # -- Embeddings --
    embedding_model: str = "all-MiniLM-L6-v2"

    # -- YOLO --
    yolo_enabled: bool = False
    yolo_model: str = "yolo11n.pt"
    yolo_confidence: float = 0.5

    # -- Server --
    host: str = "0.0.0.0"
    port: int = 8000
    log_level: str = "info"

    # -- Alert constraints --
    critical_audio_max_words: int = 25
    frame_skip: int = 3


@lru_cache()
def get_settings() -> Settings:
    """Return cached application settings (singleton)."""
    return Settings()
