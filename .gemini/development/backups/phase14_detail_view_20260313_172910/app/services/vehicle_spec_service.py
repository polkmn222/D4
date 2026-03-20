from sqlalchemy.orm import Session
from ..models import VehicleSpecification
from ..utils.sf_id import get_id
from typing import List, Optional

class VehicleSpecService:
    @staticmethod
    def create_spec(db: Session, **kwargs) -> VehicleSpecification:
        db_spec = VehicleSpecification(id=get_id("VehicleSpecification"), **kwargs)
        db.add(db_spec)
        db.commit()
        db.refresh(db_spec)
        return db_spec

    @staticmethod
    def get_specs(db: Session, record_type: Optional[str] = None) -> List[VehicleSpecification]:
        query = db.query(VehicleSpecification)
        if record_type:
            query = query.filter(VehicleSpecification.record_type == record_type)
        return query.all()

    @staticmethod
    def get_spec(db: Session, spec_id: str) -> Optional[VehicleSpecification]:
        return db.query(VehicleSpecification).filter(VehicleSpecification.id == spec_id).first()
