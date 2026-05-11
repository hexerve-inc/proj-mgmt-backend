from sqlalchemy.orm import Session
from models.sprint import Sprint
from schemas.sprint import SprintCreate, SprintUpdate

class SprintService:
    @staticmethod
    def get_all(db: Session):
        return db.query(Sprint).all()

    @staticmethod
    def get_by_id(db: Session, sprint_id: str):
        return db.query(Sprint).filter(Sprint.id == sprint_id).first()

    @staticmethod
    def create(db: Session, sprint: SprintCreate):
        sprint_data = sprint.model_dump(exclude={"task_ids"})
        db_sprint = Sprint(**sprint_data)
        db.add(db_sprint)
        db.commit()
        db.refresh(db_sprint)
        
        if sprint.task_ids:
            from models.task import Task
            db.query(Task).filter(Task.id.in_(sprint.task_ids)).update(
                {Task.sprint_id: db_sprint.id}, synchronize_session=False
            )
            db.commit()
            
        return db_sprint

    @staticmethod
    def update(db: Session, sprint_id: str, sprint: SprintUpdate):
        db_sprint = SprintService.get_by_id(db, sprint_id)
        if db_sprint:
            update_data = sprint.model_dump(exclude_unset=True)
            for key, value in update_data.items():
                setattr(db_sprint, key, value)
            db.commit()
            db.refresh(db_sprint)
        return db_sprint

    @staticmethod
    def delete(db: Session, sprint_id: str):
        db_sprint = SprintService.get_by_id(db, sprint_id)
        if db_sprint:
            db.delete(db_sprint)
            db.commit()
            return True
        return False
