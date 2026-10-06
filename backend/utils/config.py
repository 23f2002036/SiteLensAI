import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

APP_TITLE = "SiteLens AI Backend"
APP_VERSION = "0.2.0"

# Use DATABASE_URL from env when available.
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    # If DATABASE_URL is not explicitly set, fallback to local SQLite for ease of development/testing.
    DATABASE_URL = "sqlite:///sitelens.db"

CORS_ORIGINS = [
    "*",
]

