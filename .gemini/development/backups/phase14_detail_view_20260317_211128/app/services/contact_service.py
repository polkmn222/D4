from sqlalchemy.orm import Session
from typing import List, Optional
import logging
from ..models import Contact
from .base_service import BaseService

logger = logging.getLogger(__name__)

class ContactService(BaseService[Contact]):
    model = Contact
    object_name = "Contact"

    @classmethod
    def create_contact(cls, db: Session, **kwargs) -> Contact:
        return cls.create(db, **kwargs)

    @classmethod
    def get_contacts(cls, db: Session) -> List[Contact]:
        return cls.list(db)

    @classmethod
    def get_contact(cls, db: Session, contact_id: str) -> Optional[Contact]:
        return cls.get(db, contact_id)

    @classmethod
    def update_contact(cls, db: Session, contact_id: str, **kwargs) -> Optional[Contact]:
        return cls.update(db, contact_id, **kwargs)

    @classmethod
    def delete_contact(cls, db: Session, contact_id: str) -> bool:
        return cls.delete(db, contact_id)

    @classmethod
    def restore_contact(cls, db: Session, contact_id: str) -> bool:
        return cls.restore(db, contact_id)
