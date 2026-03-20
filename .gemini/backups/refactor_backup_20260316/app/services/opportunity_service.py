from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import List, Optional
import logging
from ..models import Opportunity
from ..utils.timezone import get_kst_now_naive
from .base_service import BaseService

logger = logging.getLogger(__name__)

class OpportunityService(BaseService[Opportunity]):
    model = Opportunity
    object_name = "Opportunity"

    @classmethod
    def create_opportunity(cls, db: Session, account_id: str = None, name: str = "", amount: int = 0, stage: str = "Prospecting", status: str = "Open", probability: int = 10, **kwargs) -> Opportunity:
        return cls.create(db, account_id=account_id, name=name, amount=amount, stage=stage, status=status, probability=probability, **kwargs)

    @classmethod
    def get_by_account(cls, db: Session, account_id: str) -> List[Opportunity]:
        return cls.list(db, account_id=account_id)

    @classmethod
    def get_opportunities(cls, db: Session) -> List[Opportunity]:
        return cls.list(db)

    @classmethod
    def get_opportunity(cls, db: Session, opp_id: str) -> Optional[Opportunity]:
        return cls.get(db, opp_id)

    @classmethod
    def update_opportunity(cls, db: Session, opp_id: str, **kwargs) -> Optional[Opportunity]:
        return cls.update(db, opp_id, **kwargs)

    @classmethod
    def delete_opportunity(cls, db: Session, opp_id: str) -> bool:
        return cls.delete(db, opp_id)

    @classmethod
    def restore_opportunity(cls, db: Session, opp_id: str) -> bool:
        return cls.restore(db, opp_id)

    @classmethod
    def update_stage(cls, db: Session, opp_id: str, stage: str) -> Optional[Opportunity]:
        return cls.update(db, opp_id, stage=stage)
    
    @classmethod
    def update_last_viewed(cls, db: Session, opp_id: str) -> Optional[Opportunity]:
        return cls.update(db, opp_id, last_viewed_at=get_kst_now_naive())

    @classmethod
    def get_recent_clicked(cls, db: Session, limit: int = 5) -> List[Opportunity]:
        opps = cls.list(db)
        clicked = [o for o in opps if o.last_viewed_at]
        clicked.sort(key=lambda x: x.last_viewed_at if isinstance(x.last_viewed_at, datetime) else datetime.min, reverse=True)
        if not clicked:
            clicked = opps
            clicked.sort(key=lambda x: x.created_at if isinstance(x.created_at, datetime) else datetime.min, reverse=True)
        return clicked[:limit]

    @classmethod
    def get_performance_stats(cls, db: Session, horizon_days: int = 7) -> dict:
        horizon = datetime.now() - timedelta(days=horizon_days)
        opps = cls.list(db)
        
        def safe_created_at(o):
            if not o.created_at: return datetime.min
            if isinstance(o.created_at, datetime): return o.created_at
            try: return datetime.fromisoformat(str(o.created_at))
            except: return datetime.min

        opps_filtered = [o for o in opps if safe_created_at(o) >= horizon]
        
        stages = ["Qualification", "Test Drive", "Proposal/Price Quote", "Negotiation/Review", "Closed Won", "Closed Lost"]
        performance_by_stage = []
        for stage in stages:
            amount = sum(o.amount for o in opps_filtered if o.stage == stage and o.amount)
            performance_by_stage.append({"label": stage, "amount": f"{amount:,}"})
        
        return {
            "by_stage": performance_by_stage,
            "closed_won": f"{sum(o.amount for o in opps_filtered if o.stage == 'Closed Won' and o.amount):,}",
            "total_target": 1000000000
        }

    @classmethod
    def get_ai_recommendations(cls, db: Session, limit: int = 10) -> List[Opportunity]:
        opps = cls.list(db)
        horizon_7d = datetime.now() - timedelta(days=7)
        
        def safe_created_at(o):
            if not o.created_at: return datetime.min
            if isinstance(o.created_at, datetime): return o.created_at
            try: return datetime.fromisoformat(str(o.created_at))
            except: return datetime.min

        recommends = []
        for o in opps:
            created_at = safe_created_at(o)
            if o.stage not in ["Test Drive", "Closed Won"]: continue
            if created_at < horizon_7d: continue
                
            if o.stage == "Test Drive": o.temp_display = "Hot"
            elif o.stage == "Closed Won": o.temp_display = "Warm"
            else: o.temp_display = "Cold"
                
            recommends.append(o)
                
        recommends.sort(key=lambda x: safe_created_at(x), reverse=True)
        return recommends[:limit]
