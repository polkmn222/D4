from sqlalchemy.orm import Session
from typing import List, Optional
import logging
from ..models import Campaign
from .base_service import BaseService

logger = logging.getLogger(__name__)

class CampaignService(BaseService[Campaign]):
    model = Campaign
    object_name = "Campaign"

    @classmethod
    def create_campaign(cls, db: Session, **kwargs) -> Campaign:
        return cls.create(db, **kwargs)

    @classmethod
    def update_campaign(cls, db: Session, campaign_id: str, **kwargs) -> Optional[Campaign]:
        return cls.update(db, campaign_id, **kwargs)

    @classmethod
    def delete_campaign(cls, db: Session, campaign_id: str) -> bool:
        return cls.delete(db, campaign_id)

    @classmethod
    def get_campaigns(cls, db: Session) -> List[Campaign]:
        return cls.list(db)

    @classmethod
    def get_campaign(cls, db: Session, campaign_id: str) -> Optional[Campaign]:
        return cls.get(db, campaign_id)
