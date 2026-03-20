from sqlalchemy.orm import Session
from typing import List, Optional
import logging
from db.models import Task
from backend.app.services.base_service import BaseService

logger = logging.getLogger(__name__)

class TaskService(BaseService[Task]):
    model = Task
    object_name = "Task"

    @classmethod
    def create_task(cls, db: Session, **kwargs) -> Task:
        return cls.create(db, **kwargs)

    @classmethod
    def get_tasks(cls, db: Session) -> List[Task]:
        return cls.list(db)

    @classmethod
    def get_task(cls, db: Session, task_id: str) -> Optional[Task]:
        return cls.get(db, task_id)

    @classmethod
    def update_task(cls, db: Session, task_id: str, **kwargs) -> Optional[Task]:
        return cls.update(db, task_id, **kwargs)

    @classmethod
    def delete_task(cls, db: Session, task_id: str) -> bool:
        return cls.delete(db, task_id)

    @classmethod
    def restore_task(cls, db: Session, task_id: str) -> bool:
        return cls.restore(db, task_id)
