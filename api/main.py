from fastapi import APIRouter
from api.routes import projects, tasks, teams, clients, programs, time_entries, invoices, auth

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])

api_router.include_router(projects.router, prefix="/projects", tags=["projects"])
api_router.include_router(tasks.router, prefix="/tasks", tags=["tasks"])
api_router.include_router(teams.router, prefix="/teams", tags=["teams"])
api_router.include_router(clients.router, prefix="/clients", tags=["clients"])
api_router.include_router(programs.router, prefix="/programs", tags=["programs"])
api_router.include_router(time_entries.router, prefix="/time-entries", tags=["time_entries"])
api_router.include_router(invoices.router, prefix="/invoices", tags=["invoices"])
