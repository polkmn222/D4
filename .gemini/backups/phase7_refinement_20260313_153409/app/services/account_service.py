from sqlalchemy.orm import Session
from ..models import Account
from ..utils.sf_id import get_id
from typing import List, Optional

class AccountService:
    @staticmethod
    def create_account(db: Session, status: str = "Active", **kwargs) -> Account:
        db_acc = Account(id=get_id("Account"), status=status, **kwargs)
        db.add(db_acc)
        db.commit()
        db.refresh(db_acc)
        return db_acc

    @staticmethod
    def get_accounts(db: Session) -> List[Account]:
        return db.query(Account).all()
