from sqlalchemy.orm import Session
from typing import List, Optional
import logging
from ..models import Model
from .base_service import BaseService

logger = logging.getLogger(__name__)

class ModelService(BaseService[Model]):
    model = Model
    object_name = "Model"

    @classmethod
    def create_model(cls, db: Session, **kwargs) -> Model:
        return cls.create(db, **kwargs)

    @classmethod
    def get_models(cls, db: Session) -> List[Model]:
        return cls.list(db)

    @classmethod
    def get_model(cls, db: Session, model_id: str) -> Optional[Model]:
        return cls.get(db, model_id)

    @classmethod
    def update_model(cls, db: Session, model_id: str, **kwargs) -> Optional[Model]:
        return cls.update(db, model_id, **kwargs)

    @classmethod
    def delete_model(cls, db: Session, model_id: str) -> bool:
        return cls.delete(db, model_id)
