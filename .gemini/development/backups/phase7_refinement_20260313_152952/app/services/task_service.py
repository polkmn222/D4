from sqlalchemy.orm import Session
from ..models import Task
from ..utils.sf_id import get_id
from typing import List, Optional

class TaskService:
    @staticmethod
    def create_task(db: Session, account_id: str, subject: str, **kwargs) -> Task:
        db_task = Task(id=get_id("Task"), account_id=account_id, subject=subject, **kwargs)
        db.add(db_task)
        db.commit()
        db.refresh(db_task)
        return db_task

    @staticmethod
    def get_tasks(db: Session, account_id: Optional[str] = None) -> List[Task]:
        query = db.query(Task)
        if account_id:
            query = query.filter(Task.account_id == account_id)
        return query.all()
