from core.database import SessionLocal
from services.task_watcher_service import TaskWatcherService
from api.routes.tasks import _enrich_tasks_with_watcher_data
from models.task import Task
from models.user import User
import traceback
from fastapi.encoders import jsonable_encoder

def test():
    db = SessionLocal()
    try:
        tasks = db.query(Task).all()[:5]
        user = db.query(User).first()
        if not tasks:
            print("No tasks found")
            return
            
        print("Enriching tasks...")
        result = _enrich_tasks_with_watcher_data(tasks, db, user.id)
        print("Success enriching!")
        
        print("Testing jsonable_encoder...")
        json_res = jsonable_encoder(result)
        print("Success encoding!")
        
    except Exception as e:
        traceback.print_exc()
    finally:
        db.close()

test()
