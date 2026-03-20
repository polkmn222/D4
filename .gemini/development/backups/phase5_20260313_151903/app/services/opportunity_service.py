from sqlalchemy.orm import Session
from ..models import Opportunity
from typing import List, Optional

class OpportunityService:
    @staticmethod
    def create_opportunity(db: Session, account_id: int, name: str, amount: int, stage: str, probability: int = 10, **kwargs) -> Opportunity:
        db_opp = Opportunity(
            account_id=account_id,
            name=name,
            amount=amount,
            stage=stage,
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
