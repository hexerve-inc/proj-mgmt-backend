from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from api.deps import get_db, require_permission
from schemas.workflow_status import (
    WorkflowStatusCreate,
    WorkflowStatusUpdate,
    WorkflowStatusResponse,
    WorkflowStatusReorderItem,
)
from services.workflow_status_service import WorkflowStatusService

router = APIRouter()


@router.get(
    "/{project_id}/statuses",
    response_model=list[WorkflowStatusResponse],
)
def get_project_statuses(
    project_id: str, 
    db: Session = Depends(get_db),
    checker = Depends(require_permission("workflow:read"))
):
    checker.check_scope("project", project_id)
    """List all workflow statuses for a project, ordered by group then position."""
    service = WorkflowStatusService(db)
    return service.get_statuses(project_id)


@router.post(
    "/{project_id}/statuses",
    response_model=WorkflowStatusResponse,
    status_code=201,
)
def create_project_status(
    project_id: str,
    status_in: WorkflowStatusCreate,
    db: Session = Depends(get_db),
    checker = Depends(require_permission("workflow:create"))
):
    checker.check_scope("project", project_id)
    """Create a new custom status within a project."""
    service = WorkflowStatusService(db)
    try:
        return service.create_status(project_id, status_in)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.patch(
    "/{project_id}/statuses/{status_id}",
    response_model=WorkflowStatusResponse,
)
def update_project_status(
    project_id: str,
    status_id: str,
    status_in: WorkflowStatusUpdate,
    db: Session = Depends(get_db),
    checker = Depends(require_permission("workflow:update"))
):
    checker.check_scope("project", project_id)
    """Update an existing workflow status (name, color, icon, position, group)."""
    service = WorkflowStatusService(db)
    status = service.update_status(status_id, status_in)
    if not status:
        raise HTTPException(status_code=404, detail="Status not found.")
    if status.project_id != project_id:
        raise HTTPException(status_code=404, detail="Status not found in this project.")
    return status


@router.delete(
    "/{project_id}/statuses/{status_id}",
    status_code=204,
)
def delete_project_status(
    project_id: str,
    status_id: str,
    move_to_status_id: str = Query(
        default=None,
        description="Target status ID to move tasks to before deletion.",
    ),
    db: Session = Depends(get_db),
    checker = Depends(require_permission("workflow:delete"))
):
    checker.check_scope("project", project_id)
    """Delete a workflow status. Requires move_to_status_id if tasks exist."""
    service = WorkflowStatusService(db)
    status = service.get_status(status_id)
    if not status or status.project_id != project_id:
        raise HTTPException(status_code=404, detail="Status not found in this project.")
    try:
        service.delete_status(status_id, move_to_status_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post(
    "/{project_id}/statuses/reorder",
    response_model=list[WorkflowStatusResponse],
)
def reorder_project_statuses(
    project_id: str,
    items: list[WorkflowStatusReorderItem],
    db: Session = Depends(get_db),
    checker = Depends(require_permission("workflow:reorder"))
):
    checker.check_scope("project", project_id)
    """Batch-update positions (and optionally groups) for multiple statuses."""
    service = WorkflowStatusService(db)
    return service.reorder_statuses(project_id, items)
