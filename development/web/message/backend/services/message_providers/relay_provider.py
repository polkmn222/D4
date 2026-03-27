import os
from typing import Any, Dict, Optional

import httpx

from .base import BaseMessageProvider, MessageDispatchPayload


class RelayMessageProvider(BaseMessageProvider):
    provider_name = "relay"

    @staticmethod
    def _absolute_image_url(image_url: Optional[str]) -> Optional[str]:
        if not image_url:
            return None
        if image_url.startswith("http://") or image_url.startswith("https://"):
            return image_url
        base_url = os.getenv("APP_BASE_URL", "").strip().rstrip("/")
        if base_url and image_url.startswith("/"):
            return f"{base_url}{image_url}"
        return image_url

    def send(self, db: Any, payload: MessageDispatchPayload) -> Dict[str, Any]:
        endpoint = os.getenv("RELAY_MESSAGE_ENDPOINT", "").strip()
        token = os.getenv("RELAY_MESSAGE_TOKEN", "").strip()
        if not endpoint:
            return {
                "status": "error",
                "provider": self.provider_name,
                "message": "RELAY_MESSAGE_ENDPOINT is not configured.",
            }
        if not token:
            return {
                "status": "error",
                "provider": self.provider_name,
                "message": "RELAY_MESSAGE_TOKEN is not configured.",
            }

        outbound = payload.to_dict()
        outbound["image_url"] = self._absolute_image_url(payload.image_url)
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

        with httpx.Client() as client:
            response = client.post(endpoint, json=outbound, headers=headers, timeout=20)

        if response.status_code >= 400:
            return {
                "status": "error",
                "provider": self.provider_name,
                "message": response.text or f"Relay provider error ({response.status_code}).",
            }

        try:
            data = response.json()
        except ValueError:
            data = {}

        relay_data = data.get("data") if isinstance(data, dict) else None
        if isinstance(relay_data, dict):
            return {
                "status": relay_data.get("status", "success"),
                "provider": relay_data.get("provider", self.provider_name),
                "provider_message_id": relay_data.get("provider_message_id"),
                "message": relay_data.get("message", "Relay provider accepted the message."),
            }

        return {
            "status": "success",
            "provider": self.provider_name,
            "message": "Relay provider accepted the message.",
        }
