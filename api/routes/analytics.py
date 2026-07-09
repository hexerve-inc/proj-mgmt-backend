from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from api.deps import get_db, get_current_user
from models.user import User
from services.analytics_service import AnalyticsService
from schemas.analytics import (
    UserTaskMetric,
    ProjectTaskMetric,
    DueDateTask,
    UserWorkload,
    AnalyticsSummary,
)

router = APIRouter()


@router.get("/tasks-per-user", response_model=list[UserTaskMetric])
def get_tasks_per_user(
    project_id: str | None = Query(None, description="Filter to a specific project"),
    include_unassigned: bool = Query(False, description="Include unassigned bucket"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Aggregated task counts grouped by assignee user."""
    service = AnalyticsService(db)
    return service.get_tasks_per_user(
        project_id=project_id, include_unassigned=include_unassigned
    )


@router.get("/tasks-per-project", response_model=list[ProjectTaskMetric])
def get_tasks_per_project(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Aggregated task counts grouped by project."""
    service = AnalyticsService(db)
    return service.get_tasks_per_project()


@router.get("/tasks-by-due-date", response_model=list[DueDateTask])
def get_tasks_by_due_date(
    date: date = Query(..., description="Target date in YYYY-MM-DD format"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """All tasks due on a specific date, enriched with assignee/project info."""
    service = AnalyticsService(db)
    return service.get_tasks_by_due_date(target_date=date)


@router.get("/user-workload", response_model=list[UserWorkload])
def get_user_workload(
    project_id: str | None = Query(None, description="Filter to a specific project"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Active task count per user, sorted descending by workload."""
    service = AnalyticsService(db)
    return service.get_user_workload(project_id=project_id)


@router.get("/summary", response_model=AnalyticsSummary)
def get_analytics_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Top-level analytics summary with aggregate counts."""
    service = AnalyticsService(db)
    return service.get_summary()
