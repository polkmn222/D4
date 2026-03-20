from sqlalchemy.orm import Session
from ..models import Product
from typing import List, Optional

class ProductService:
    @staticmethod
    def create_product(db: Session, **kwargs) -> Product:
        db_prod = Product(**kwargs)
        db.add(db_prod)
        db.commit()
        db.refresh(db_prod)
        return db_prod

    @staticmethod
    def get_products(db: Session) -> List[Product]:
        return db.query(Product).all()
