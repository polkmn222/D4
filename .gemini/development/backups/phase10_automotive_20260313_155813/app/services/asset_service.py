from sqlalchemy.orm import Session
from ..models import Asset
from ..utils.sf_id import get_id
from typing import List, Optional

class AssetService:
    @staticmethod
    def create_asset(db: Session, contact_id: str, name: str, product_id: Optional[str] = None, **kwargs) -> Asset:
        db_asset = Asset(id=get_id("Asset"), contact_id=contact_id, name=name, product_id=product_id, **kwargs)
        db.add(db_asset)
        db.commit()
        db.refresh(db_asset)
        return db_asset

    @staticmethod
    def get_assets(db: Session, contact_id: Optional[int] = None) -> List[Asset]:
        query = db.query(Asset)
        if contact_id:
            query = query.filter(Asset.contact_id == contact_id)
        return query.all()
