from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class MessageDispatchPayload:
    contact_id: str
    record_type: str
    content: str
    subject: Optional[str] = None
    template_id: Optional[str] = None
    attachment_id: Optional[str] = None
    attachment_path: Optional[str] = None
    attachment_name: Optional[str] = None
    attachment_provider_key: Optional[str] = None
    image_url: Optional[str] = None

    def to_dict(self) -> Dict[str, Optional[str]]:
        return {
            "contact_id": self.contact_id,
            "record_type": self.record_type,
            "content": self.content,
            "subject": self.subject,
            "template_id": self.template_id,
            "attachment_id": self.attachment_id,
            "attachment_path": self.attachment_path,
            "attachment_name": self.attachment_name,
            "attachment_provider_key": self.attachment_provider_key,
            "image_url": self.image_url,
        }


class BaseMessageProvider:
    provider_name = "base"

    def send(self, db: Any, payload: MessageDispatchPayload) -> Dict[str, Any]:
        raise NotImplementedError
