import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from core.config import settings
from core.database import engine, Base

# Import all models to ensure they are registered with Base metadata
from models import user, project, task, team, client, program, time_entry, invoice
from api.main import api_router

# from contextlib import asynccontextmanager
# from alembic.config import Config
# from alembic import command

# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     # Run migrations on startup
#     alembic_cfg = Config("alembic.ini")
#     db_url = os.environ.get("DATABASE_URL")
#     if db_url:
#         alembic_cfg.set_main_option("sqlalchemy.url", db_url)
#     command.upgrade(alembic_cfg, "head")

#     # Create tables in the DB (useful for SQLite fast iterations)
#     yield

Base.metadata.create_all(bind=engine)
app = FastAPI(title=settings.PROJECT_NAME)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Connect API Router with v1 prefix
app.include_router(api_router, prefix="/api/v1")

@app.get("/")
def read_root():
    return {"message": "Welcome to the Project Management API"}
