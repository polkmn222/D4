from sqlalchemy.orm import Session
from typing import List, Optional
import logging
from ..models import VehicleSpecification
from .base_service import BaseService

logger = logging.getLogger(__name__)

class VehicleSpecService(BaseService[VehicleSpecification]):
    model = VehicleSpecification
    object_name = "VehicleSpecification"

    @classmethod
    def create_spec(cls, db: Session, **kwargs) -> VehicleSpecification:
        return cls.create(db, **kwargs)

    @classmethod
    def update_vehicle_spec(cls, db: Session, spec_id: str, **kwargs) -> Optional[VehicleSpecification]:
        return cls.update(db, spec_id, **kwargs)

    @classmethod
    def delete_vehicle_spec(cls, db: Session, spec_id: str) -> bool:
        return cls.delete(db, spec_id)

    @classmethod
    def get_vehicle_specs(cls, db: Session, record_type: Optional[str] = None) -> List[VehicleSpecification]:
        return cls.list(db, record_type=record_type)

    @classmethod
    def get_vehicle_spec(cls, db: Session, spec_id: str) -> Optional[VehicleSpecification]:
        return cls.get(db, spec_id)
