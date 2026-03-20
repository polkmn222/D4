from sqlalchemy.orm import Session
from typing import List, Optional
import logging
from ..models import Product
from .base_service import BaseService

logger = logging.getLogger(__name__)

class ProductService(BaseService[Product]):
    model = Product
    object_name = "Product"

    @classmethod
    def create_product(cls, db: Session, **kwargs) -> Product:
        return cls.create(db, **kwargs)

    @classmethod
    def update_product(cls, db: Session, product_id: str, **kwargs) -> Optional[Product]:
        return cls.update(db, product_id, **kwargs)

    @classmethod
    def delete_product(cls, db: Session, product_id: str) -> bool:
        return cls.delete(db, product_id)

    @classmethod
    def restore_product(cls, db: Session, product_id: str) -> bool:
        return cls.restore(db, product_id)

    @classmethod
    def get_products(cls, db: Session) -> List[Product]:
        return cls.list(db)

    @classmethod
    def get_product(cls, db: Session, product_id: str) -> Optional[Product]:
        return cls.get(db, product_id)
