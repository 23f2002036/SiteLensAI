"""
SiteLens AI — FastAPI Application Entry Point

Orchestration engine that:
  1. Initializes VLM engine on startup
  2. Initializes RAG pipeline (embeddings, FAISS, retriever)
  3. Initializes STT engine (Groq Whisper)
  4. Initializes audit database
  5. Mounts all route handlers
  6. Serves the static web UI
  7. Provides CORS for dashboard access
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI

from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.config import get_settings
from app.models.vlm_engine import create_vlm_engine
from app.routes import alerts, detect, rag_query, stream, voice, audit

# ── Logging ──────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s │ %(name)-30s │ %(levelname)-7s │ %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("sitelens")

# ── Paths ────────────────────────────────────────────────────────────────

STATIC_DIR = Path(__file__).parent / "static"
SOP_DIR = Path(__file__).resolve().parent.parent / "data" / "sops"


# ── Lifespan ─────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize engines on startup, cleanup on shutdown."""
    settings = get_settings()

    logger.info("=" * 60)
    logger.info("  SiteLens AI — Starting up")
    logger.info("  VLM Backend : %s", settings.vlm_backend.value)
    logger.info("  Vector Store: %s", settings.vector_backend.value)
    logger.info("  YOLO Enabled: %s", settings.yolo_enabled)
    logger.info("=" * 60)

    # ── 1. Initialize VLM engine ──
    vlm_engine = None
    try:
        vlm_engine = create_vlm_engine(settings)
        detect.set_vlm_engine(vlm_engine)
        stream.set_vlm_engine(vlm_engine)
        logger.info("✓ VLM engine initialized (%s)", settings.vlm_backend.value)
    except Exception as e:
        logger.error("✗ Failed to initialize VLM engine: %s", e)
        logger.warning("  Server will start but /api/detect will return 503.")

    # ── 2. Initialize RAG pipeline ──
    retriever = None
    try:
        from app.rag.embeddings import EmbeddingEngine
        from app.rag.vector_store import FAISSVectorStore
        from app.rag.retriever import SOPRetriever

        embedder = EmbeddingEngine()
        store = FAISSVectorStore(
            index_path=settings.faiss_index_path,
            dimension=embedder.dimension,
        )

        # Auto-ingest SOPs if the index is empty
        if store.count == 0 and SOP_DIR.exists():
            logger.info("FAISS index is empty — auto-ingesting SOPs from %s", SOP_DIR)
            from app.rag.ingest import ingest_directory
            ingest_directory(
                directory=str(SOP_DIR),
                store_path=settings.faiss_index_path,
            )
            # Reload the store after ingestion
            store = FAISSVectorStore(
                index_path=settings.faiss_index_path,
                dimension=embedder.dimension,
            )

        retriever = SOPRetriever(vector_store=store, embedding_engine=embedder)
        rag_query.set_retriever(retriever)
        detect.set_retriever(retriever)
        stream.set_retriever(retriever)
        logger.info("✓ RAG pipeline initialized (%d documents)", store.count)
    except Exception as e:
        logger.error("✗ Failed to initialize RAG pipeline: %s", e)
        logger.warning("  RAG queries will return fallback responses.")

    # ── 3. Initialize STT engine (Groq Whisper) ──
    try:
        from app.models.stt_engine import create_stt_engine
        stt_engine = create_stt_engine(settings)
        voice.set_stt_engine(stt_engine)
        voice.set_retriever(retriever)
        logger.info("✓ STT engine initialized (whisper)")
    except Exception as e:
        logger.error("✗ Failed to initialize STT engine: %s", e)

    # ── 4. Initialize Rule Engine ──
    try:
        from app.hazard.rule_engine import RuleEngine
        rule_engine = RuleEngine(settings)
        detect.set_rule_engine(rule_engine)
        stream.set_rule_engine(rule_engine)
        logger.info("✓ Rule engine initialized")
    except Exception as e:
        logger.error("✗ Failed to initialize rule engine: %s", e)

    # ── 5. Initialize Audit Database ──
    try:
        from app.models.database import AuditDatabase
        db = AuditDatabase()
        await db.initialize()
        detect.set_audit_db(db)
        alerts.set_audit_db(db)
        audit.set_audit_db(db)
        logger.info("✓ Audit database initialized")
    except Exception as e:
        logger.error("✗ Failed to initialize audit database: %s", e)

    yield

    logger.info("SiteLens AI — Shutting down")


# ── App ──────────────────────────────────────────────────────────────────

app = FastAPI(
    title="SiteLens AI",
    description="Hazardous Construction Site Alert & RAG Orchestration System",
    version="2.0.0",
    lifespan=lifespan,
)

# CORS — allow dashboard and development origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Tighten in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routes ───────────────────────────────────────────────────────────────

app.include_router(detect.router)
app.include_router(stream.router)
app.include_router(alerts.router)
app.include_router(rag_query.router)
app.include_router(voice.router)
app.include_router(audit.router)


# ── Static files & SPA fallback ─────────────────────────────────────────

if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/")
async def serve_ui():
    """Serve the main SiteLens AI web interface."""
    index = STATIC_DIR / "index.html"
    if index.exists():
        return FileResponse(str(index))
    return {
        "service": "SiteLens AI",
        "version": "2.0.0",
        "status": "running",
        "endpoints": {
            "detect": "/api/detect",
            "stream": "/ws/stream",
            "alerts": "/api/alerts",
            "alerts_sse": "/api/alerts/stream",
            "rag_query": "/api/query",
            "voice_query": "/api/voice/query",
            "voice_transcribe": "/api/voice/transcribe",
            "audit_incidents": "/api/audit/incidents",
            "docs": "/docs",
        },
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    settings = get_settings()
    return {
        "status": "healthy",
        "vlm_backend": settings.vlm_backend.value,
        "vector_backend": settings.vector_backend.value,
        "yolo_enabled": settings.yolo_enabled,
        "rag_enabled": True,
        "stt_enabled": True,
        "audit_enabled": True,
    }

