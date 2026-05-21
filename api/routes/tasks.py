from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from api.deps import get_db
from schemas.task import TaskCreate, TaskResponse, TaskUpdate
from services.task_service import TaskService
from services.project_service import ProjectService

router = APIRouter()

@router.get("/", response_model=list[TaskResponse])
def get_tasks(db: Session = Depends(get_db)):
    service = TaskService(db)
    return service.get_tasks()

@router.post("/", response_model=TaskResponse)
def create_task(task_in: TaskCreate, db: Session = Depends(get_db)):
    project_service = ProjectService(db)
    if not project_service.get_project(task_in.project_id):
        raise HTTPException(status_code=404, detail="Project not found")
        
    service = TaskService(db)
    try:
        return service.create_task(task_in)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

@router.get("/project/{project_id}", response_model=list[TaskResponse])
def get_project_tasks(project_id: str, db: Session = Depends(get_db)):
    service = TaskService(db)
    return service.get_tasks_for_project(project_id)

@router.get("/{task_id}", response_model=TaskResponse)
def get_task(task_id: str, db: Session = Depends(get_db)):
    service = TaskService(db)
    task = service.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

@router.patch("/{task_id}", response_model=TaskResponse)
def update_task(task_id: str, task_in: TaskUpdate, db: Session = Depends(get_db)):
    service = TaskService(db)
    try:
        task = service.update_task(task_id, task_in)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

@router.delete("/{task_id}")
def delete_task(task_id: str, db: Session = Depends(get_db)):
    service = TaskService(db)
    task = service.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Actually perform the delete
    db.delete(task)
    db.commit()
    return {"message": "Task deleted successfully"}
