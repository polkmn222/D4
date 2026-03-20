from sqlalchemy.orm import Session
from typing import List, Optional
import logging
from ..models import Account
from .base_service import BaseService

logger = logging.getLogger(__name__)

class AccountService(BaseService[Account]):
    model = Account
    object_name = "Account"

    @classmethod
    def create_account(cls, db: Session, status: str = "Active", **kwargs) -> Account:
        return cls.create(db, status=status, **kwargs)

    @classmethod
    def get_accounts(cls, db: Session) -> List[Account]:
        return cls.list(db)

    @classmethod
    def get_account(cls, db: Session, account_id: str) -> Optional[Account]:
        return cls.get(db, account_id)

    @classmethod
    def update_account(cls, db: Session, account_id: str, **kwargs) -> Optional[Account]:
        return cls.update(db, account_id, **kwargs)

    @classmethod
    def delete_account(cls, db: Session, account_id: str) -> bool:
        return cls.delete(db, account_id)

    @classmethod
    def restore_account(cls, db: Session, account_id: str) -> bool:
        return cls.restore(db, account_id)
