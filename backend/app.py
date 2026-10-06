from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import OperationalError

import database
from database import Base, SessionLocal, engine
from seed import seed_database
from utils.config import APP_TITLE, APP_VERSION, CORS_ORIGINS

# Import APIRouters
from routes import auth, mobile, web, tasks, reports


@asynccontextmanager
async def lifespan(_: FastAPI):
    try:
        Base.metadata.create_all(bind=engine)
        database.database_ready = True

        # Auto-seed default data
        db = SessionLocal()
        try:
            seed_database(db)
        finally:
            db.close()

    except OperationalError:
        database.database_ready = False
        print(
            "[SiteLens AI] Database connection failed at startup. "
            "If PostgreSQL was recreated with new credentials, remove the old postgres_data volume or update DATABASE_URL."
        )
    yield


import os
import httpx
from fastapi.staticfiles import StaticFiles


def _placeholder_value(value: str | None) -> bool:
    if value is None:
        return True
    cleaned = value.strip()
    if not cleaned or cleaned.lower() in {"none", "null", "n/a", "na"}:
        return True
    lowered = cleaned.lower()
    return any(marker in lowered for marker in ("your-", "placeholder", "changeme", "example", "dummy", "replace"))


def _print_vlm_status() -> None:
    groq_key = os.getenv("GROQ_API_KEY")
    grok_key = os.getenv("GROK_API_KEY")
    ollama_host = os.getenv("OLLAMA_HOST")
    ollama_model = os.getenv("OLLAMA_MODEL")
    groq_model = os.getenv("GROQ_MODEL")
    grok_model = os.getenv("GROK_MODEL")

    if groq_key and not _placeholder_value(groq_key):
        print(f"[SiteLens AI] VLM backend: Groq | model: {groq_model or 'qwen/qwen3.6-27b'} | status: configured")
        return

    if grok_key and not _placeholder_value(grok_key):
        print(f"[SiteLens AI] VLM backend: Grok | model: {grok_model or 'grok-2-vision-latest'} | status: configured")
        return

    if ollama_host and not _placeholder_value(ollama_host):
        try:
            response = httpx.get(f"{ollama_host.rstrip('/')}/api/tags", timeout=5.0)
            healthy = response.status_code == 200
        except Exception:
            healthy = False
        print(
            f"[SiteLens AI] VLM backend: Ollama | host: {ollama_host} | model: {ollama_model or 'qwen3-vl'} | status: {'reachable' if healthy else 'not reachable'}"
        )
        return

    print("[SiteLens AI] VLM backend: not configured | status: no valid model key/host found")


# Ensure upload directories exist
os.makedirs("uploads/images", exist_ok=True)
os.makedirs("uploads/audio", exist_ok=True)
_print_vlm_status()

app = FastAPI(
    title=APP_TITLE,
    version=APP_VERSION,
    lifespan=lifespan,
)

# Serve uploaded static media files
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")


# CORS middleware for Web (React, Next.js) and Mobile clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root() -> dict[str, str]:
    return {
        "service": APP_TITLE,
        "status": "running",
        "health": "/health",
        "docs": "/docs",
    }


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


# Register API Routers
app.include_router(auth.router)
app.include_router(mobile.router)
app.include_router(web.router)
app.include_router(tasks.router)
app.include_router(reports.router)
