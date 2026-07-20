import os
import time
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from alembic.config import Config
from alembic import command
 
from core.config import settings
from core.database import engine, Base
# Import all models to ensure they are registered with Base metadata
from models import user, project, task, team, client, program, time_entry, invoice
from api.main import api_router
 
# Helper function to trigger Alembic migrations safely on Neon
def run_migrations():
    print("Initializing Neon database migration...")
    # Locate your alembic.ini file (assumed to be in your project root)
    ini_path = os.path.join(os.path.dirname(__file__), "alembic.ini")
    cfg = Config(ini_path)
    # Use the environment variable if available, otherwise fall back to settings
    database_url = os.getenv("DATABASE_URL") or settings.DATABASE_URL
    if database_url:
        # Strip pooler flags if present, as Alembic needs a direct connection
        cfg.set_main_option("sqlalchemy.url", database_url)
    # Retry loop to handle Neon "waking up" from a cold start
    for attempt in range(3):
        try:
            command.upgrade(cfg, "head")
            print("Database migration completed successfully!")
            break
        except Exception as e:
            print(f"Neon compute waking up, retrying... (Attempt {attempt + 1}/3). Error: {e}")
            time.sleep(3)
    else:
        print("Migration failed after multiple attempts.")
 
# Lifespan context manager to handle startup tasks
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Runs before the application starts accepting requests
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
    print("Unhandled exception:", exc)
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
    return {"message": "Welcome to the Project Management API"}
