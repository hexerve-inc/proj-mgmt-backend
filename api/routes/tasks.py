from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from api.deps import get_db, get_current_user
from schemas.task import TaskCreate, TaskResponse, TaskUpdate
from schemas.task_watcher import (
    WatchStatusResponse,
    TaskWatchersListResponse,
    TaskWatcherUserResponse,
    AssignWatcherRequest,
)
from services.task_service import TaskService
from services.project_service import ProjectService
from services.notification_service import NotificationService
from services.notification_events import NotificationEvent
from services.task_watcher_service import TaskWatcherService
from models.notification_preference import NotificationEventType
from models.user import User

router = APIRouter()


def _emit_task_notifications(
    db_factory,
    event: NotificationEvent,
):
    """Background task wrapper — creates its own DB session for async dispatch."""
    from core.database import SessionLocal

    db = SessionLocal()
    try:
        service = NotificationService(db)
        service.emit_sync(event)
    finally:
        db.close()


def _enrich_tasks_with_watcher_data(
    tasks, db: Session, current_user_id: str
) -> list[dict]:
    """Inject watcher_count, is_watching, and watchers list into task responses."""
    if not tasks:
        return []
    watcher_service = TaskWatcherService(db)
    task_ids = [t.id for t in tasks]
    counts = watcher_service.get_watcher_counts_bulk(task_ids)
    watching = watcher_service.get_watching_status_bulk(task_ids, current_user_id)
    watchers_bulk = watcher_service.get_watchers_bulk(task_ids)
    result = []
    for t in tasks:
        task_dict = TaskResponse.model_validate(t).model_dump()
        task_dict["watcher_count"] = counts.get(t.id, 0)
        task_dict["is_watching"] = watching.get(t.id, False)
        task_dict["watchers"] = watchers_bulk.get(t.id, [])
        result.append(task_dict)
    return result


@router.get("/")
def get_tasks(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = TaskService(db)
    tasks = service.get_tasks()
    return _enrich_tasks_with_watcher_data(tasks, db, current_user.id)

@router.post("/", response_model=TaskResponse)
def create_task(
    task_in: TaskCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project_service = ProjectService(db)
    if not project_service.get_project(task_in.project_id):
        raise HTTPException(status_code=404, detail="Project not found")
        
    service = TaskService(db)
    try:
        task = service.create_task(task_in)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    # Auto-watch: task creator becomes first watcher
    watcher_service = TaskWatcherService(db)
    watcher_service.watch_task(task.id, current_user.id)

    # Emit TASK_CREATED notification
    background_tasks.add_task(
        _emit_task_notifications,
        None,
        NotificationEvent(
            event_type=NotificationEventType.TASK_CREATED,
            actor_id=current_user.id,
            entity_id=task.id,
            entity_type="task",
            project_id=task.project_id,
            metadata={
                "task_code": task.task_code,
                "task_title": task.title,
                "description": task.description or "",
            },
        ),
    )

    # Return enriched response with watcher data
    return _enrich_tasks_with_watcher_data([task], db, current_user.id)[0]

@router.get("/project/{project_id}")
def get_project_tasks(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = TaskService(db)
    tasks = service.get_tasks_for_project(project_id)
    return _enrich_tasks_with_watcher_data(tasks, db, current_user.id)

@router.get("/{task_id}")
def get_task(
    task_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = TaskService(db)
    task = service.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return _enrich_tasks_with_watcher_data([task], db, current_user.id)[0]

@router.patch("/{task_id}", response_model=TaskResponse)
def update_task(
    task_id: str,
    task_in: TaskUpdate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = TaskService(db)

    # Capture current state BEFORE update for change detection
    old_task = service.get_task(task_id)
    if not old_task:
        raise HTTPException(status_code=404, detail="Task not found")

    old_status_id = old_task.status_id
    old_assignee_id = old_task.assignee_id
    old_priority = old_task.priority.value if old_task.priority else None
    old_due_date = str(old_task.due_date) if old_task.due_date else None
    old_sprint_id = old_task.sprint_id
    old_status_name = old_task.status.name if old_task.status else old_status_id
    old_assignee_name = old_task.assignee.name if old_task.assignee else None

    try:
        task = service.update_task(task_id, task_in)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    # Determine which events to emit based on what changed
    update_data = task_in.model_dump(exclude_unset=True)
    base_metadata = {
        "task_code": task.task_code,
        "task_title": task.title,
    }

    # Status change
    if "status_id" in update_data and update_data["status_id"] != old_status_id:
        new_status_name = task.status.name if task.status else update_data["status_id"]
        background_tasks.add_task(
            _emit_task_notifications,
            None,
            NotificationEvent(
                event_type=NotificationEventType.TASK_STATUS_CHANGED,
                actor_id=current_user.id,
                entity_id=task.id,
                entity_type="task",
                project_id=task.project_id,
                metadata={
                    **base_metadata,
                    "old_status": old_status_name,
                    "new_status": new_status_name,
                },
            ),
        )

    # Assignee change
    if "assignee_id" in update_data and update_data["assignee_id"] != old_assignee_id:
        new_assignee_id = update_data["assignee_id"]
        new_assignee_name = task.assignee.name if task.assignee else None

        if old_assignee_id and new_assignee_id:
            # Reassignment
            background_tasks.add_task(
                _emit_task_notifications,
                None,
                NotificationEvent(
                    event_type=NotificationEventType.TASK_REASSIGNED,
                    actor_id=current_user.id,
                    entity_id=task.id,
                    entity_type="task",
                    project_id=task.project_id,
                    metadata={
                        **base_metadata,
                        "old_assignee_id": old_assignee_id,
                        "old_assignee_name": old_assignee_name or "Unassigned",
                        "new_assignee_id": new_assignee_id,
                        "new_assignee_name": new_assignee_name or "Unassigned",
                    },
                ),
            )
        elif new_assignee_id:
            # First assignment
            background_tasks.add_task(
                _emit_task_notifications,
                None,
                NotificationEvent(
                    event_type=NotificationEventType.TASK_ASSIGNED,
                    actor_id=current_user.id,
                    entity_id=task.id,
                    entity_type="task",
                    project_id=task.project_id,
                    metadata={
                        **base_metadata,
                        "assignee_id": new_assignee_id,
                        "assignee_name": new_assignee_name or "Unknown",
                    },
                ),
            )

    # Priority change
    if "priority" in update_data:
        new_priority = update_data["priority"]
        if new_priority != old_priority:
            background_tasks.add_task(
                _emit_task_notifications,
                None,
                NotificationEvent(
                    event_type=NotificationEventType.TASK_PRIORITY_CHANGED,
                    actor_id=current_user.id,
                    entity_id=task.id,
                    entity_type="task",
                    project_id=task.project_id,
                    metadata={
                        **base_metadata,
                        "old_priority": old_priority or "None",
                        "new_priority": new_priority,
                    },
                ),
            )

    # Due date change
    if "due_date" in update_data:
        new_due_date = str(update_data["due_date"]) if update_data["due_date"] else None
        if new_due_date != old_due_date:
            background_tasks.add_task(
                _emit_task_notifications,
                None,
                NotificationEvent(
                    event_type=NotificationEventType.TASK_DUE_DATE_CHANGED,
                    actor_id=current_user.id,
                    entity_id=task.id,
                    entity_type="task",
                    project_id=task.project_id,
                    metadata={
                        **base_metadata,
                        "old_due_date": old_due_date,
                        "new_due_date": new_due_date,
                    },
                ),
            )

    # Sprint change
    if "sprint_id" in update_data and update_data["sprint_id"] != old_sprint_id:
        from models.sprint import Sprint
        old_sprint = db.query(Sprint).filter(Sprint.id == old_sprint_id).first() if old_sprint_id else None
        new_sprint = db.query(Sprint).filter(Sprint.id == update_data["sprint_id"]).first() if update_data["sprint_id"] else None
        background_tasks.add_task(
            _emit_task_notifications,
            None,
            NotificationEvent(
                event_type=NotificationEventType.TASK_SPRINT_CHANGED,
                actor_id=current_user.id,
                entity_id=task.id,
                entity_type="task",
                project_id=task.project_id,
                metadata={
                    **base_metadata,
                    "old_sprint": old_sprint.name if old_sprint else "Backlog",
                    "new_sprint": new_sprint.name if new_sprint else "Backlog",
                },
            ),
        )

    # General details update (title, description, story_points)
    detail_fields = {"title", "description", "story_points"}
    changed_details = [f for f in detail_fields if f in update_data]
    if changed_details and not any(f in update_data for f in ("status_id", "assignee_id", "priority", "due_date", "sprint_id")):
        background_tasks.add_task(
            _emit_task_notifications,
            None,
            NotificationEvent(
                event_type=NotificationEventType.TASK_DETAILS_UPDATED,
                actor_id=current_user.id,
                entity_id=task.id,
                entity_type="task",
                project_id=task.project_id,
                metadata={
                    **base_metadata,
                    "changed_fields": ", ".join(changed_details),
                },
            ),
        )

    return task

@router.delete("/{task_id}")
def delete_task(
    task_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = TaskService(db)

    # Capture task info before deletion for the notification
    task = service.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    task_code = task.task_code
    task_title = task.title
    project_id = task.project_id

    success = service.delete_task(task_id)
    if not success:
        raise HTTPException(status_code=404, detail="Task not found")

    # Emit TASK_DELETED notification
    background_tasks.add_task(
        _emit_task_notifications,
        None,
        NotificationEvent(
            event_type=NotificationEventType.TASK_DELETED,
            actor_id=current_user.id,
            entity_id=task_id,
            entity_type="task",
            project_id=project_id,
            metadata={
                "task_code": task_code,
                "task_title": task_title,
            },
        ),
    )

    return {"message": "Task deleted successfully"}


# ── Task Watcher endpoints ───────────────────────────────────────

@router.post("/{task_id}/watch", response_model=WatchStatusResponse)
def watch_task(
    task_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Current user starts watching the task."""
    service = TaskService(db)
    task = service.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    watcher_service = TaskWatcherService(db)
    watcher_service.watch_task(task_id, current_user.id)
    return WatchStatusResponse(
        watching=True,
        watcher_count=watcher_service.get_watcher_count(task_id),
    )


@router.delete("/{task_id}/watch", response_model=WatchStatusResponse)
def unwatch_task(
    task_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Current user stops watching the task."""
    service = TaskService(db)
    task = service.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    watcher_service = TaskWatcherService(db)
    watcher_service.unwatch_task(task_id, current_user.id)
    return WatchStatusResponse(
        watching=False,
        watcher_count=watcher_service.get_watcher_count(task_id),
    )


@router.get("/{task_id}/watchers", response_model=TaskWatchersListResponse)
def get_task_watchers(
    task_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all users watching this task."""
    service = TaskService(db)
    task = service.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    watcher_service = TaskWatcherService(db)
    watchers = watcher_service.get_task_watchers_with_since(task_id)
    return TaskWatchersListResponse(
        watchers=[TaskWatcherUserResponse(**w) for w in watchers],
        count=len(watchers),
    )


@router.get("/{task_id}/watch/status", response_model=WatchStatusResponse)
def get_watch_status(
    task_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Check if current user is watching this task."""
    watcher_service = TaskWatcherService(db)
    return WatchStatusResponse(
        watching=watcher_service.is_watching(task_id, current_user.id),
        watcher_count=watcher_service.get_watcher_count(task_id),
    )


@router.post("/{task_id}/watchers", response_model=WatchStatusResponse)
def assign_task_watcher(
    task_id: str,
    request: AssignWatcherRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Assign a specific user as a watcher."""
    service = TaskService(db)
    task = service.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    watcher_service = TaskWatcherService(db)
    watcher_service.watch_task(task_id, request.user_id)
    return WatchStatusResponse(
        watching=watcher_service.is_watching(task_id, current_user.id),
        watcher_count=watcher_service.get_watcher_count(task_id),
    )


@router.delete("/{task_id}/watchers/{user_id}", response_model=WatchStatusResponse)
def remove_task_watcher(
    task_id: str,
    user_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Remove a specific user from watching the task."""
    service = TaskService(db)
    task = service.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    watcher_service = TaskWatcherService(db)
    watcher_service.unwatch_task(task_id, user_id)
    return WatchStatusResponse(
        watching=watcher_service.is_watching(task_id, current_user.id),
        watcher_count=watcher_service.get_watcher_count(task_id),
    )
