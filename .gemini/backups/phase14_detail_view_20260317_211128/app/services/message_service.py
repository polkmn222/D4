from sqlalchemy.orm import Session
from typing import List, Optional
import logging
from ..models import Message
from .base_service import BaseService

logger = logging.getLogger(__name__)

class MessageService(BaseService[Message]):
    model = Message
    object_name = "Message"

    @classmethod
    def create_message(cls, db: Session, contact: str, content: str, direction: str = "Outbound", status: str = "Sent", **kwargs) -> Message:
        return cls.create(db, contact=contact, content=content, direction=direction, status=status, **kwargs)

    @classmethod
    def get_messages(cls, db: Session, contact: Optional[str] = None) -> List[Message]:
        return cls.list(db, contact=contact)

    @classmethod
    def get_message(cls, db: Session, message_id: str) -> Optional[Message]:
        return cls.get(db, message_id)

    @classmethod
    def update_message(cls, db: Session, message_id: str, **kwargs) -> Optional[Message]:
        return cls.update(db, message_id, **kwargs)

    @classmethod
    def delete_message(cls, db: Session, message_id: str) -> bool:
        return cls.delete(db, message_id)
