"""
SiteLens AI — RAG Retriever

Semantic search over ingested SOP documents.
Takes a natural-language query (from VLM hazard analysis or worker voice),
retrieves the most relevant SOP chunks, and returns them as context
for the prompt engine.
"""

from __future__ import annotations

import logging
from typing import Any, Optional

from app.rag.embeddings import EmbeddingEngine, get_embedding_engine
from app.rag.vector_store import FAISSVectorStore, SearchResult

logger = logging.getLogger("sitelens.rag.retriever")


class SOPRetriever:
    """Retrieves relevant SOP chunks using semantic similarity search."""

    def __init__(
        self,
        vector_store: FAISSVectorStore,
        embedding_engine: Optional[EmbeddingEngine] = None,
    ):
        self.store = vector_store
        self.embedder = embedding_engine or get_embedding_engine()

    async def retrieve(
        self,
        query: str,
        top_k: int = 5,
        min_score: float = 0.2,
    ) -> list[dict[str, Any]]:
        """
        Retrieve relevant SOP chunks for a query.

        Parameters
        ----------
        query : natural language search query
        top_k : max results to return
        min_score : minimum cosine similarity threshold

        Returns
        -------
        List of dicts with keys: content, source_file, section, score, rank
        """
        if self.store.count == 0:
            logger.warning("Vector store is empty — no documents to search.")
            return []

        # Embed query
        query_vec = self.embedder.embed(query)

        # Search
        results: list[SearchResult] = self.store.search(query_vec, top_k=top_k)

        # Filter by minimum score and format
        output = []
        for r in results:
            if r.score < min_score:
                continue
            output.append({
                "content": r.chunk.content,
                "source_file": r.chunk.source_file,
                "section": r.chunk.section,
                "score": round(r.score, 4),
                "rank": r.rank,
                "metadata": r.chunk.metadata,
            })

        logger.info(
            "Retrieved %d/%d results for query: '%.60s…'",
            len(output),
            len(results),
            query,
        )
        return output

    async def retrieve_for_hazard(
        self,
        hazard_type: str,
        description: str,
        top_k: int = 3,
    ) -> list[str]:
        """
        Convenience method: retrieve SOP text chunks relevant
        to a specific hazard. Returns just the text content
        ready for prompt injection.
        """
        query = f"Construction safety SOP: {hazard_type}. {description}"
        results = await self.retrieve(query, top_k=top_k)
        return [r["content"] for r in results]
