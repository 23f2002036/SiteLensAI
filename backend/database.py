from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from utils.config import DATABASE_URL

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, pool_pre_ping=True, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

database_ready = False


def get_db():
    if not database_ready:
        raise HTTPException(
            status_code=503,
            detail="Database is unavailable. Check PostgreSQL credentials or reset the local volume.",
        )
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
