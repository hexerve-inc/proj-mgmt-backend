from fastapi import APIRouter
from api.routes import projects, tasks, teams, clients, programs, time_entries, invoices, auth, users, portfolios, sprints, workflow_statuses, custom_filters, notifications

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])

api_router.include_router(projects.router, prefix="/projects", tags=["projects"])
api_router.include_router(workflow_statuses.router, prefix="/projects", tags=["workflow_statuses"])
api_router.include_router(tasks.router, prefix="/tasks", tags=["tasks"])
api_router.include_router(teams.router, prefix="/teams", tags=["teams"])
api_router.include_router(clients.router, prefix="/clients", tags=["clients"])
api_router.include_router(programs.router, prefix="/programs", tags=["programs"])
api_router.include_router(portfolios.router, prefix="/portfolios", tags=["portfolios"])
api_router.include_router(time_entries.router, prefix="/time-entries", tags=["time_entries"])
api_router.include_router(invoices.router, prefix="/invoices", tags=["invoices"])
api_router.include_router(sprints.router, prefix="/sprints", tags=["sprints"])
api_router.include_router(custom_filters.router, prefix="/projects", tags=["custom_filters"])
api_router.include_router(notifications.router, prefix="/users", tags=["notifications"])


