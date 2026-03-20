from sqlalchemy.orm import Session
from ..models import Campaign
from ..utils.sf_id import get_id
from typing import List, Optional

class CampaignService:
    @staticmethod
    def create_campaign(db: Session, **kwargs) -> Campaign:
        db_cmp = Campaign(id=get_id("Campaign"), **kwargs)
        db.add(db_cmp)
        db.commit()
        db.refresh(db_cmp)
        return db_cmp

    @staticmethod
    def get_campaigns(db: Session) -> List[Campaign]:
        return db.query(Campaign).all()

    @staticmethod
    def get_campaign(db: Session, campaign_id: str) -> Optional[Campaign]:
        return db.query(Campaign).filter(Campaign.id == campaign_id).first()
