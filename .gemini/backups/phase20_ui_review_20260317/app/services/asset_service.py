from sqlalchemy.orm import Session
from typing import List, Optional
import logging
from ..models import Asset
from .base_service import BaseService

logger = logging.getLogger(__name__)

class AssetService(BaseService[Asset]):
    model = Asset
    object_name = "Asset"

    @classmethod
    def create_asset(cls, db: Session, name: str, account: Optional[str] = None, product: Optional[str] = None, **kwargs) -> Asset:
        return cls.create(db, name=name, account=account, product=product, **kwargs)

    @classmethod
    def get_assets(cls, db: Session, account: Optional[str] = None) -> List[Asset]:
        return cls.list(db, account=account)

    @classmethod
    def get_asset(cls, db: Session, asset_id: str) -> Optional[Asset]:
        return cls.get(db, asset_id)

    @classmethod
    def update_asset(cls, db: Session, asset_id: str, **kwargs) -> Optional[Asset]:
        return cls.update(db, asset_id, **kwargs)

    @classmethod
    def delete_asset(cls, db: Session, asset_id: str) -> bool:
        return cls.delete(db, asset_id)

    @classmethod
    def restore_asset(cls, db: Session, asset_id: str) -> bool:
        return cls.restore(db, asset_id)
