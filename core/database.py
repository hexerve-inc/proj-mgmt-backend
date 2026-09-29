import os
import sys
import traceback
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from core.config import settings

raw_db_url = os.getenv("DATABASE_URL") or settings.DATABASE_URL or ""
print(f"[DATABASE.PY] Raw DATABASE_URL: {repr(raw_db_url)}", flush=True)

db_url = raw_db_url.strip() if raw_db_url else ""

# Normalize postgres:// to postgresql:// for SQLAlchemy compatibility
if db_url.startswith("postgres://"):
    print("[DATABASE.PY] Normalizing 'postgres://' scheme to 'postgresql://'", flush=True)
    db_url = db_url.replace("postgres://", "postgresql://", 1)

try:
    if not db_url:
        print("[DATABASE.PY WARNING] No DATABASE_URL provided. Using in-memory SQLite to prevent crash.", flush=True)
        engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    else:
        connect_args = {"check_same_thread": False} if db_url.startswith("sqlite") else {}
        print(f"[DATABASE.PY] Initializing SQLAlchemy engine with: {db_url.split('@')[-1] if '@' in db_url else db_url}", flush=True)
        engine = create_engine(db_url, connect_args=connect_args)
        print("[DATABASE.PY] Engine created successfully!", flush=True)
except Exception as exc:
    print(f"[DATABASE.PY ERROR] create_engine failed for URL {repr(raw_db_url)}: {exc}", flush=True)
    traceback.print_exc()
    print("[DATABASE.PY] Falling back to in-memory SQLite engine so application can still boot and serve debug endpoints.", flush=True)
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
