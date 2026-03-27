from sqlalchemy.orm import Session
from typing import List, Optional
import logging
from db.models import MessageTemplate
from web.backend.app.services.base_service import BaseService
from web.backend.app.services.record_delete_service import RecordDeleteService
from web.backend.app.utils.error_handler import handle_agent_errors

logger = logging.getLogger(__name__)

class MessageTemplateService(BaseService[MessageTemplate]):
    model = MessageTemplate
    object_name = "MessageTemplate"
    TEMPLATE_IMAGE_ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/jpg"}
    TEMPLATE_IMAGE_ALLOWED_EXTENSIONS = {".jpg", ".jpeg"}
    TEMPLATE_IMAGE_MAX_BYTES = 500 * 1024

    @classmethod
    def validate_template_image_upload(
        cls,
        filename: Optional[str],
        content_type: Optional[str],
        file_size: int,
    ) -> None:
        suffix = ""
        if filename and "." in filename:
            suffix = f".{filename.rsplit('.', 1)[-1].lower()}"
        if content_type not in cls.TEMPLATE_IMAGE_ALLOWED_CONTENT_TYPES or suffix not in cls.TEMPLATE_IMAGE_ALLOWED_EXTENSIONS:
            raise ValueError("Only JPG images under 500KB are allowed.")
        if file_size > cls.TEMPLATE_IMAGE_MAX_BYTES:
            raise ValueError("Only JPG images under 500KB are allowed.")

    @classmethod
    def _validate_and_normalize_template(cls, kwargs: dict) -> dict:
        content = kwargs.get("content", "")
        record_type = kwargs.get("record_type", "SMS")
        
        # Calculate byte length (2 bytes for non-ASCII/Korean, 1 byte for ASCII)
        byte_len = 0
        for char in content:
            byte_len += 2 if ord(char) > 127 else 1
            
        # 1. SMS to LMS auto-switch
        if record_type == "SMS" and byte_len > 90:
            record_type = "LMS"
            kwargs["record_type"] = "LMS"
            # Since the user was on SMS form, subject was hidden. Clear it for consistency.
            kwargs["subject"] = None
            
        # 2. 2000 byte limit for LMS/MMS
        if byte_len > 2000:
            raise ValueError(f"Content exceeds maximum limit of 2000 bytes (Current: {byte_len} bytes)")
            
        # 3. Field normalization
        if record_type == "SMS":
            kwargs["subject"] = None
            kwargs["attachment_id"] = None
            kwargs["image_url"] = None
            kwargs["file_path"] = None
        elif record_type == "LMS":
            kwargs["attachment_id"] = None
            kwargs["image_url"] = None
            kwargs["file_path"] = None
            
        return kwargs

    @classmethod
    @handle_agent_errors
    def create_template(cls, db: Session, **kwargs) -> MessageTemplate:
        normalized_kwargs = cls._validate_and_normalize_template(kwargs)
        return cls.create(db, **normalized_kwargs)

    @classmethod
    @handle_agent_errors
    def get_templates(cls, db: Session) -> List[MessageTemplate]:
        return cls.list(db)

    @classmethod
    @handle_agent_errors
    def get_template(cls, db: Session, template_id: str) -> Optional[MessageTemplate]:
        return cls.get(db, template_id)

    @classmethod
    @handle_agent_errors
    def update_template(cls, db: Session, template_id: str, **kwargs) -> Optional[MessageTemplate]:
        normalized_kwargs = cls._validate_and_normalize_template(kwargs)
        return cls.update(db, template_id, **normalized_kwargs)

    @classmethod
    @handle_agent_errors
    def update_image_url(cls, db: Session, template_id: str, image_url: str) -> Optional[MessageTemplate]:
        return cls.update(db, template_id, image_url=image_url)

    @classmethod
    @handle_agent_errors
    def delete_template(cls, db: Session, template_id: str) -> bool:
        return RecordDeleteService.delete_message_template(db, template_id)

    @classmethod
    @handle_agent_errors
    def restore_template(cls, db: Session, template_id: str) -> bool:
        return cls.delete(db, template_id)
