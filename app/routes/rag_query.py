"""
SiteLens AI — RAG query route (Phase 2 stub)

Worker voice query endpoint. Accepts transcribed audio,
retrieves relevant SOPs, and returns contextual guidance.
"""

from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

logger = logging.getLogger("sitelens.routes.rag_query")

router = APIRouter(prefix="/api", tags=["rag"])

# Module-level reference (set in Phase 2)
_retriever = None


def set_retriever(retriever):
    """Called from main.py to inject the RAG retriever."""
    global _retriever
    _retriever = retriever


class QueryRequest(BaseModel):
    query: str
    top_k: int = 5


class QueryResponse(BaseModel):
    query: str
    answer: str
    sop_references: list[dict]
    has_results: bool


@router.post("/query", response_model=QueryResponse)
async def rag_query(request: QueryRequest):
    """
    Worker voice query endpoint.

    Accepts transcribed audio text, retrieves relevant SOPs,
    and returns contextual safety guidance.
    """
    if _retriever is None:
        # Phase 2 not yet deployed — return helpful fallback
        return QueryResponse(
            query=request.query,
            answer=(
                "RAG pipeline is not yet initialized. "
                "Please follow standard construction site safety procedures. "
                "Contact your supervisor for specific SOP guidance."
            ),
            sop_references=[],
            has_results=False,
        )

    try:
        results = await _retriever.retrieve(request.query, top_k=request.top_k)
        if not results:
            return QueryResponse(
                query=request.query,
                answer="No matching SOPs found for your query. Contact your supervisor.",
                sop_references=[],
                has_results=False,
            )

        return QueryResponse(
            query=request.query,
            answer=results[0].get("content", ""),
            sop_references=results,
            has_results=True,
        )
    except Exception as e:
        logger.exception("RAG query failed")
        raise HTTPException(status_code=500, detail=f"RAG query error: {e}")
