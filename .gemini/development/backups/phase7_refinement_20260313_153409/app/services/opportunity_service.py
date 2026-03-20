from sqlalchemy.orm import Session
from ..models import Opportunity
from ..utils.sf_id import get_id
from typing import List, Optional

class OpportunityService:
    @staticmethod
    def create_opportunity(db: Session, account_id: str, name: str, amount: int, stage: str, status: str = "Open", probability: int = 10, **kwargs) -> Opportunity:
        db_opp = Opportunity(
            id=get_id("Opportunity"),
            account_id=account_id,
            name=name,
            amount=amount,
            stage=stage,
            status=status,
            probability=probability,
            **kwargs
        )
        db.add(db_opp)
        db.commit()
        db.refresh(db_opp)
        return db_opp

    @staticmethod
    def get_opportunities(db: Session) -> List[Opportunity]:
        return db.query(Opportunity).all()
