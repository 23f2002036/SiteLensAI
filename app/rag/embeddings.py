"""
SiteLens AI — Embedding Generation

Generates vector embeddings for text using sentence-transformers.
Used for both SOP document ingestion and query-time embedding.
"""

from __future__ import annotations

import logging
from functools import lru_cache
from typing import Optional

import numpy as np

from app.config import get_settings

logger = logging.getLogger("sitelens.rag.embeddings")


class EmbeddingEngine:
    """Generates text embeddings using sentence-transformers."""

    def __init__(self, model_name: Optional[str] = None):
        from sentence_transformers import SentenceTransformer

        self.model_name = model_name or get_settings().embedding_model
        logger.info("Loading embedding model: %s", self.model_name)
        self.model = SentenceTransformer(self.model_name)
        self.dimension = self.model.get_sentence_embedding_dimension()
        logger.info(
            "Embedding model loaded (dim=%d, model=%s)",
            self.dimension,
            self.model_name,
        )

    def embed(self, text: str) -> np.ndarray:
        """Embed a single text string → 1D numpy array."""
        return self.model.encode(text, normalize_embeddings=True)

    def embed_batch(self, texts: list[str], batch_size: int = 32) -> np.ndarray:
        """Embed a batch of texts → 2D numpy array (N, dim)."""
        return self.model.encode(
            texts,
            batch_size=batch_size,
            normalize_embeddings=True,
            show_progress_bar=len(texts) > 100,
        )


@lru_cache()
def get_embedding_engine() -> EmbeddingEngine:
    """Return a singleton EmbeddingEngine."""
    return EmbeddingEngine()
