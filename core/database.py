import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from core.config import settings

db_url = settings.DATABASE_URL or os.getenv("DATABASE_URL") or ""
if not db_url:
    print("[WARNING] DATABASE_URL is not set! Using fallback SQLite database to prevent application crash.", flush=True)
    db_url = "sqlite:///./fallback.db"

engine = create_engine(
    db_url,
    connect_args={"check_same_thread": False} if db_url.startswith("sqlite") else {}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
