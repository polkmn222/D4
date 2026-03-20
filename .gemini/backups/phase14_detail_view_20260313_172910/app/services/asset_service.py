from sqlalchemy.orm import Session
from ..models import Asset
from ..utils.sf_id import get_id
from typing import List, Optional

class AssetService:
    @staticmethod
    def create_asset(db: Session, account_id: str, name: str, product_id: Optional[str] = None, **kwargs) -> Asset:
        db_asset = Asset(id=get_id("Asset"), account_id=account_id, name=name, product_id=product_id, **kwargs)
        db.add(db_asset)
        db.commit()
        db.refresh(db_asset)
        return db_asset

    @staticmethod
    def get_assets(db: Session, account_id: Optional[str] = None) -> List[Asset]:
        query = db.query(Asset)
        if account_id:
            query = query.filter(Asset.account_id == account_id)
        return query.all()

    @staticmethod
    def get_asset(db: Session, asset_id: str) -> Optional[Asset]:
        return db.query(Asset).filter(Asset.id == asset_id).first()
