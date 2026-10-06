"""
SiteLens AI — Voice Routes (STT + RAG Hands-Free Guidance)

Endpoints:
  POST /api/voice/query      — Upload audio → transcribe → RAG search → response
  POST /api/voice/transcribe — Raw transcription only
"""

from __future__ import annotations

import logging
from typing import Any, Optional

from fastapi import APIRouter, File, HTTPException, UploadFile

logger = logging.getLogger("sitelens.routes.voice")

router = APIRouter(prefix="/api/voice", tags=["voice"])

# ── Module-level singletons (injected via main.py lifespan) ──
_stt_engine = None
_retriever = None


def set_stt_engine(engine):
    global _stt_engine
    _stt_engine = engine


def set_retriever(retriever):
    global _retriever
    _retriever = retriever


@router.post("/transcribe")
async def transcribe_audio(audio: UploadFile = File(...)):
    """Transcribe audio to text using Groq Whisper."""
    if _stt_engine is None:
        raise HTTPException(status_code=503, detail="STT engine not initialized.")

    audio_bytes = await audio.read()
    if not audio_bytes:
        raise HTTPException(status_code=400, detail="Empty audio file.")

    try:
        result = await _stt_engine.transcribe(
            audio_bytes=audio_bytes,
            filename=audio.filename or "audio.wav",
        )
        return result
    except Exception as e:
        logger.error("Transcription failed: %s", e)
        raise HTTPException(status_code=500, detail=f"Transcription error: {e}")


@router.post("/query")
async def voice_query(audio: UploadFile = File(...)):
    """
    Full voice pipeline:
    1. Transcribe audio to text
    2. Search RAG for relevant SOPs
    3. Return transcription + relevant SOPs
    """
    if _stt_engine is None:
        raise HTTPException(status_code=503, detail="STT engine not initialized.")

    audio_bytes = await audio.read()
    if not audio_bytes:
        raise HTTPException(status_code=400, detail="Empty audio file.")

    # 1. Transcribe
    try:
        transcription = await _stt_engine.transcribe(
            audio_bytes=audio_bytes,
            filename=audio.filename or "audio.wav",
        )
    except Exception as e:
        logger.error("Transcription failed: %s", e)
        raise HTTPException(status_code=500, detail=f"Transcription error: {e}")

    query_text = transcription.get("text", "")
    if not query_text:
        return {
            "transcription": transcription,
            "query": "",
            "results": [],
            "answer": "Could not understand the audio. Please try again.",
        }

    # 2. RAG search
    results = []
    answer = f"I heard: \"{query_text}\". "

    if _retriever:
        try:
            results = await _retriever.retrieve(query_text, top_k=3)
            if results:
                # Build answer from retrieved SOPs
                sop_texts = [r["content"][:300] for r in results]
                answer += "Based on our safety procedures: " + " ".join(sop_texts[:2])
            else:
                answer += "No specific safety procedures found for this query. Please follow standard site safety protocols."
        except Exception as e:
            logger.error("RAG retrieval failed: %s", e)
            answer += "RAG search unavailable. Please consult your safety manual."
    else:
        answer += "Safety document search is not available at this time."

    return {
        "transcription": transcription,
        "query": query_text,
        "results": results,
        "answer": answer,
    }
