from sqlalchemy.orm import Session
from typing import List, Optional
import logging
from ..models import Task
from .base_service import BaseService

logger = logging.getLogger(__name__)

class TaskService(BaseService[Task]):
    model = Task
    object_name = "Task"

    @classmethod
    def create_task(cls, db: Session, subject: str, account: Optional[str] = None, **kwargs) -> Task:
        return cls.create(db, subject=subject, account=account, **kwargs)

    @classmethod
    def get_tasks(cls, db: Session, account: Optional[str] = None) -> List[Task]:
        return cls.list(db, account=account)

    @classmethod
    def get_task(cls, db: Session, task_id: str) -> Optional[Task]:
        return cls.get(db, task_id)

    @classmethod
    def update_task(cls, db: Session, task_id: str, **kwargs) -> Optional[Task]:
        return cls.update(db, task_id, **kwargs)
