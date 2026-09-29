import os
import sys
import traceback
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from core.config import settings

raw_db_url = os.getenv("DATABASE_URL") or settings.DATABASE_URL or ""
print(f"[DATABASE.PY] Raw DATABASE_URL: {repr(raw_db_url)}", flush=True)

db_url = raw_db_url.strip() if raw_db_url else ""

def init_engine(url: str):
    if not url:
        print("[DATABASE.PY WARNING] No DATABASE_URL provided. Using in-memory SQLite fallback.", flush=True)
        return create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    
    # Candidate URLs to try in order of compatibility
    candidates = []
    
    norm_url = url
    if norm_url.startswith("postgres://"):
        norm_url = norm_url.replace("postgres://", "postgresql://", 1)
    
    # 1. Prefer psycopg2 if postgresql:// without explicit driver (widely compatible)
    if norm_url.startswith("postgresql://") and not norm_url.startswith("postgresql+"):
        candidates.append(norm_url.replace("postgresql://", "postgresql+psycopg2://", 1))
        candidates.append(norm_url)
        candidates.append(norm_url.replace("postgresql://", "postgresql+psycopg://", 1))
    elif norm_url.startswith("postgresql+psycopg://"):
        candidates.append(norm_url)
        candidates.append(norm_url.replace("postgresql+psycopg://", "postgresql+psycopg2://", 1))
    elif norm_url.startswith("postgresql+psycopg2://"):
        candidates.append(norm_url)
        candidates.append(norm_url.replace("postgresql+psycopg2://", "postgresql+psycopg://", 1))
    else:
        candidates.append(norm_url)

    last_error = None
    for candidate in candidates:
        try:
            connect_args = {"check_same_thread": False} if candidate.startswith("sqlite") else {}
            masked = candidate.split("@")[-1] if "@" in candidate else candidate
            dialect_name = candidate.split(":")[0]
            print(f"[DATABASE.PY] Testing engine candidate with dialect '{dialect_name}' ({masked})...", flush=True)
            eng = create_engine(candidate, connect_args=connect_args)
            # Force dialect to load its DBAPI driver immediately to catch missing driver errors early
            _ = eng.dialect.dbapi
            print(f"[DATABASE.PY] Successfully initialized engine using dialect '{dialect_name}'!", flush=True)
            return eng
        except Exception as exc:
            last_error = exc
            print(f"[DATABASE.PY WARNING] Dialect '{candidate.split(':')[0]}' failed: {exc}", flush=True)
            
    print(f"[DATABASE.PY ERROR] All database engine candidates failed. Last error: {last_error}", flush=True)
    traceback.print_exc()
    print("[DATABASE.PY] Falling back to in-memory SQLite engine so application can still boot and serve debug endpoints.", flush=True)
    return create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})

engine = init_engine(db_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
