from sqlalchemy.orm import Session
from typing import List, Optional
import logging
from ..models import MessageTemplate
from .base_service import BaseService

logger = logging.getLogger(__name__)

class MessageTemplateService(BaseService[MessageTemplate]):
    model = MessageTemplate
    object_name = "MessageTemplate"

    @classmethod
    def create_template(cls, db: Session, name: str, body: str, subject: Optional[str] = None, record_type: str = "SMS") -> MessageTemplate:
        return cls.create(db, name=name, body=body, subject=subject, record_type=record_type)

    @classmethod
    def get_templates(cls, db: Session) -> List[MessageTemplate]:
        return cls.list(db)

    @classmethod
    def get_template(cls, db: Session, template_id: str) -> Optional[MessageTemplate]:
        return cls.get(db, template_id)

    @classmethod
    def update_template(cls, db: Session, template_id: str, **kwargs) -> Optional[MessageTemplate]:
        return cls.update(db, template_id, **kwargs)

    @classmethod
    def delete_template(cls, db: Session, template_id: str) -> bool:
        return cls.delete(db, template_id)
