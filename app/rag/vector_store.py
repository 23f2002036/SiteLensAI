"""
SiteLens AI — Vector Store (FAISS Backend)

Stores and retrieves vectorized document chunks using FAISS
for local development. Designed to be swappable with Supabase
pgvector for production.
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Optional

import numpy as np

from app.config import get_settings

logger = logging.getLogger("sitelens.rag.vector_store")


@dataclass
class DocumentChunk:
    """A chunk of a safety document with metadata."""

    content: str
    metadata: dict[str, Any] = field(default_factory=dict)
    chunk_id: str = ""
    source_file: str = ""
    section: str = ""


@dataclass
class SearchResult:
    """A search result from the vector store."""

    chunk: DocumentChunk
    score: float
    rank: int


class FAISSVectorStore:
    """
    Local FAISS-based vector store.

    Index and metadata are persisted to disk so they survive restarts.
    """

    def __init__(self, index_path: Optional[str] = None, dimension: int = 384):
        import faiss

        self.index_path = Path(index_path or get_settings().faiss_index_path)
        self.dimension = dimension
        self.chunks: list[DocumentChunk] = []

        # Try loading existing index
        idx_file = self.index_path / "index.faiss"
        meta_file = self.index_path / "metadata.json"

        if idx_file.exists() and meta_file.exists():
            logger.info("Loading existing FAISS index from %s", self.index_path)
            self.index = faiss.read_index(str(idx_file))
            with open(meta_file, "r", encoding="utf-8") as f:
                raw = json.load(f)
            self.chunks = [DocumentChunk(**c) for c in raw]
            logger.info(
                "Loaded %d chunks (dim=%d)", len(self.chunks), self.index.d
            )
        else:
            logger.info("Creating new FAISS index (dim=%d)", dimension)
            self.index = faiss.IndexFlatIP(dimension)  # Inner product (cosine with normalized vecs)

    def add(self, chunks: list[DocumentChunk], embeddings: np.ndarray):
        """Add document chunks and their embeddings to the store."""
        if len(chunks) != embeddings.shape[0]:
            raise ValueError("Chunks and embeddings count mismatch.")

        self.index.add(embeddings.astype(np.float32))
        self.chunks.extend(chunks)
        logger.info("Added %d chunks. Total: %d", len(chunks), len(self.chunks))

    def search(self, query_embedding: np.ndarray, top_k: int = 5) -> list[SearchResult]:
        """Search for the most similar chunks to the query embedding."""
        if self.index.ntotal == 0:
            return []

        query = query_embedding.reshape(1, -1).astype(np.float32)
        scores, indices = self.index.search(query, min(top_k, self.index.ntotal))

        results = []
        for rank, (score, idx) in enumerate(zip(scores[0], indices[0])):
            if idx < 0 or idx >= len(self.chunks):
                continue
            results.append(SearchResult(
                chunk=self.chunks[idx],
                score=float(score),
                rank=rank + 1,
            ))

        return results

    def save(self):
        """Persist index and metadata to disk."""
        import faiss

        self.index_path.mkdir(parents=True, exist_ok=True)
        idx_file = self.index_path / "index.faiss"
        meta_file = self.index_path / "metadata.json"

        faiss.write_index(self.index, str(idx_file))
        with open(meta_file, "w", encoding="utf-8") as f:
            json.dump([asdict(c) for c in self.chunks], f, indent=2)

        logger.info("Saved FAISS index to %s (%d chunks)", self.index_path, len(self.chunks))

    @property
    def count(self) -> int:
        return self.index.ntotal
