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
    def create_opportunity(cls, db: Session, contact: str = None, name: str = "", amount: int = 0, stage: str = "Prospecting", status: str = "Open", probability: int = 10, **kwargs) -> Opportunity:
        # Sync amount with asset price if asset is provided
        from .asset_service import AssetService
        asset_id = kwargs.get('asset')
        if asset_id:
            asset = AssetService.get_asset(db, asset_id)
            if asset and asset.price:
                amount = asset.price
        return cls.create(db, contact=contact, name=name, amount=amount, stage=stage, status=status, probability=probability, **kwargs)

    @classmethod
    def get_by_contact(cls, db: Session, contact: str) -> List[Opportunity]:
        return cls.list(db, contact=contact)

    @classmethod
    def get_opportunities(cls, db: Session) -> List[Opportunity]:
        opps = cls.list(db)
        # Use a robust sort like in get_recent_clicked
        def parse_date(d):
            if not d: return datetime.min
            if isinstance(d, datetime): return d
            try: return datetime.fromisoformat(str(d))
            except: return datetime.min
            
        opps.sort(key=lambda x: parse_date(x.created_at), reverse=True)
        return opps

    @classmethod
    def get_opportunity(cls, db: Session, opp_id: str) -> Optional[Opportunity]:
        return cls.get(db, opp_id)

    @classmethod
    def update_opportunity(cls, db: Session, opp_id: str, **kwargs) -> Optional[Opportunity]:
        # Sync amount with asset price if asset is updated or already exists
        from .asset_service import AssetService
        asset_id = kwargs.get('asset')
        if asset_id:
            asset = AssetService.get_asset(db, asset_id)
            if asset and asset.price:
                kwargs['amount'] = asset.price
        elif 'amount' not in kwargs:
            # If asset is not in kwargs, check current asset
            opp = cls.get(db, opp_id)
            if opp and opp.asset:
                asset = AssetService.get_asset(db, opp.asset)
                if asset and asset.price:
                    kwargs['amount'] = asset.price
        
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
    def toggle_follow(cls, db: Session, opp_id: str, enabled: bool) -> Optional[Opportunity]:
        return cls.update(db, opp_id, is_followed=enabled)
    
    @classmethod
    def update_last_viewed(cls, db: Session, opp_id: str) -> Optional[Opportunity]:
        return cls.update(db, opp_id, last_viewed_at=get_kst_now_naive())

    @classmethod
    def get_recent_clicked(cls, db: Session, limit: int = 5) -> List[Opportunity]:
        opps = cls.list(db)
        # Filter for opportunities that have been viewed
        viewed_opps = [o for o in opps if o.last_viewed_at]
        
        def parse_date(d):
            if not d: return datetime.min
            if isinstance(d, datetime): return d
            try: return datetime.fromisoformat(str(d))
            except: return datetime.min

        # Sort the viewed opportunities by creation date in reverse chronological order
        viewed_opps.sort(key=lambda x: parse_date(x.created_at), reverse=True)
        
        return viewed_opps[:limit]

    @classmethod
    def get_performance_stats(cls, db: Session, horizon_days: int = 7) -> dict:
        horizon = get_kst_now_naive() - timedelta(days=horizon_days)
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
        from ..models import Contact
        # Fetch only Opportunities where the associated Contact has a phone number
        all_opps = db.query(Opportunity).join(Contact, Opportunity.contact == Contact.id)\
            .filter(Opportunity.deleted_at == None, Contact.deleted_at == None)\
            .filter(Contact.phone != None, Contact.phone != "")\
            .all()
            
        horizon_7d = get_kst_now_naive() - timedelta(days=7)
        
        def safe_created_at(o):
            if not o.created_at: return datetime.min
            if isinstance(o.created_at, datetime): return o.created_at
            try: return datetime.fromisoformat(str(o.created_at))
            except: return datetime.min

        recommends = []
        for o in all_opps:
            created_at = safe_created_at(o)
            if o.stage not in ["Test Drive", "Closed Won"]: continue
            if created_at < horizon_7d: continue
                
            if o.stage == "Test Drive": o.temp_display = "Hot"
            elif o.stage == "Closed Won": o.temp_display = "Warm"
            else: o.temp_display = "Cold"
                
            recommends.append(o)
                
        recommends.sort(key=lambda x: safe_created_at(x), reverse=True)
        return recommends[:limit]
