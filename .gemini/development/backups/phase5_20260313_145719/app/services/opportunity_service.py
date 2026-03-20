from sqlalchemy.orm import Session
from ..models import Opportunity
from typing import List, Optional

class OpportunityService:
    @staticmethod
    def create_opportunity(db: Session, contact_id: int, name: str, amount: int = 0, **kwargs) -> Opportunity:
        db_opp = Opportunity(contact_id=contact_id, name=name, amount=amount, **kwargs)
        db.add(db_opp)
        db.commit()
        db.refresh(db_opp)
        return db_opp

    @staticmethod
    def get_opportunities(db: Session, contact_id: Optional[int] = None) -> List[Opportunity]:
        query = db.query(Opportunity)
        if contact_id:
            query = query.filter(Opportunity.contact_id == contact_id)
        return query.all()
