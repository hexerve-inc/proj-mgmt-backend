import os
import sys
import time

# ── 1. IMMEDIATE BOOTSTRAP LOGGING FOR VERCEL RUNTIME ────────────────────────
print("=" * 80, flush=True)
print("[VERCEL LOGS] EARLY RUNTIME BOOTSTRAP", flush=True)
print(f"DATABASE_URL: {repr(os.getenv('DATABASE_URL'))}", flush=True)
print("--- ALL ENVIRONMENT VARIABLES (os.environ) ---", flush=True)
for k, v in sorted(os.environ.items()):
    print(f"  {k} = {v}", flush=True)
print("=" * 80, flush=True)
sys.stdout.flush()
# ─────────────────────────────────────────────────────────────────────────────

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from alembic.config import Config
from alembic import command
 
from core.config import settings
from core.debug_env import print_env_to_vercel_logs, get_env_dump
from core.database import engine, Base
# Import all models to ensure they are registered with Base metadata
from models import user, project, task, team, client, program, time_entry, invoice
from api.main import api_router

# Helper function to trigger Alembic migrations safely on Neon
def run_migrations():
    print("Initializing Neon database migration...", flush=True)
    # Locate your alembic.ini file (assumed to be in your project root)
    ini_path = os.path.join(os.path.dirname(__file__), "alembic.ini")
    cfg = Config(ini_path)
    # Use the environment variable if available, otherwise fall back to settings
    raw_db_url = os.getenv("DATABASE_URL") or settings.DATABASE_URL or ""
    database_url = raw_db_url.strip() if raw_db_url else ""
    if database_url.startswith("postgres://"):
        print("[MIGRATIONS] Normalizing 'postgres://' to 'postgresql://' for Alembic", flush=True)
        database_url = database_url.replace("postgres://", "postgresql://", 1)
    
    try:
        import psycopg  # noqa: F401
    except ImportError:
        if database_url.startswith("postgresql://") and not database_url.startswith("postgresql+"):
            database_url = database_url.replace("postgresql://", "postgresql+psycopg2://", 1)
        elif database_url.startswith("postgresql+psycopg://"):
            database_url = database_url.replace("postgresql+psycopg://", "postgresql+psycopg2://", 1)
        
    print(f"[MIGRATIONS] Using DATABASE_URL: {repr(database_url)}", flush=True)
    if database_url:
        # Strip pooler flags if present, as Alembic needs a direct connection
        cfg.set_main_option("sqlalchemy.url", database_url)
    else:
        print("[MIGRATIONS WARNING] DATABASE_URL is not set or empty! Skipping migrations.", flush=True)
        return
    # Retry loop to handle Neon "waking up" from a cold start
    for attempt in range(3):
        try:
            command.upgrade(cfg, "head")
            print("Database migration completed successfully!", flush=True)
            break
        except Exception as e:
            print(f"Neon compute waking up, retrying... (Attempt {attempt + 1}/3). Error: {e}", flush=True)
            time.sleep(3)
    else:
        print("Migration failed after multiple attempts.", flush=True)

# Lifespan context manager to handle startup tasks
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Runs before the application starts accepting requests
    print_env_to_vercel_logs(context="APP_STARTUP_LIFESPAN")
    run_migrations()
    yield

# Initialize FastAPI with the lifespan handler
app = FastAPI(title=settings.PROJECT_NAME, lifespan=lifespan) 
ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "https://proj-mgmt-fe-two.vercel.app"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from fastapi.responses import JSONResponse
from starlette.requests import Request
import traceback

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Ensure CORS headers are present even on unhandled 500 errors."""
    print("Unhandled exception:", exc, flush=True)
    traceback.print_exc()
    origin = request.headers.get("origin")
    headers = {}
    if origin in ALLOWED_ORIGINS:
        headers["Access-Control-Allow-Origin"] = origin
        headers["Access-Control-Allow-Credentials"] = "true"
        
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
        headers=headers
    )

# Connect API Router with v1 prefix
app.include_router(api_router, prefix="/api/v1")

@app.get("/")
def read_root():
    print_env_to_vercel_logs(context="HTTP_GET_ROOT /")
    return {
        "message": "Welcome to the Project Management API",
        "database_url_configured": bool(os.getenv("DATABASE_URL") or settings.DATABASE_URL),
        "debug_url": "/debug-env",
        "api_v1_debug_url": "/api/v1/debug-env"
    }

@app.get("/debug-env")
def debug_environment(show_all: bool = False):
    """
    Explicitly dumps environment variables (especially DATABASE_URL)
    to Vercel runtime logs and returns a summary in the JSON response.
    Pass ?show_all=true to include all environment variables in response.
    """
    print_env_to_vercel_logs(context="HTTP_DEBUG_ENDPOINT /debug-env")
    dump = get_env_dump()
    res = {
        "status": "success",
        "message": "Environment variables successfully logged to Vercel logs! Check your Vercel deployment logs dashboard.",
        "database_url": dump["database_url"] or "NOT_SET",
        "database_related": dump["database_related"],
        "app_variables": dump["app_variables"],
    }
    if show_all:
        res["all_variables"] = dump["all_variables"]
    return res
