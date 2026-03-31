import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, Optional

import httpx

from .base import BaseMessageProvider, MessageDispatchPayload


class SuremMessageProvider(BaseMessageProvider):
    provider_name = "surem"
    TOKEN_URL = "https://rest.surem.com/api/v1/auth/token"
    SMS_URL = "https://rest.surem.com/api/v1/send/sms"
    MMS_URL = "https://rest.surem.com/api/v1/send/mms"
    IMAGE_URL = "https://rest.surem.com/api/v1/image"
    _cached_token: Optional[str] = None
    _token_expires_at: Optional[datetime] = None

    @staticmethod
    def _env(name: str) -> str:
        return os.getenv(name, "").strip()

    @classmethod
    def _env_any(cls, *names: str) -> str:
        for name in names:
            value = cls._env(name)
            if value:
                return value
        return ""

    @classmethod
    def credentials_configured(cls) -> bool:
        return bool(cls._env_any("SUREM_USER_CODE", "SUREM_AUTH_userCode")) and bool(
            cls._env_any("SUREM_SECRET_KEY", "SUREM_AUTH_secretKey")
        )

    @classmethod
    def _token_is_valid(cls) -> bool:
        if not cls._cached_token or not cls._token_expires_at:
            return False
        return datetime.now(timezone.utc) < cls._token_expires_at

    @classmethod
    def get_access_token(cls, force_refresh: bool = False) -> str:
        if not force_refresh and cls._token_is_valid():
            return cls._cached_token or ""

        user_code = cls._env_any("SUREM_USER_CODE", "SUREM_AUTH_userCode")
        secret_key = cls._env_any("SUREM_SECRET_KEY", "SUREM_AUTH_secretKey")
        if not user_code or not secret_key:
            raise ValueError("SUREM_USER_CODE and SUREM_SECRET_KEY must be configured.")

        with httpx.Client() as client:
            response = client.post(
                cls._env_any("SUREM_AUTH_URL") or cls.TOKEN_URL,
                headers={"Content-Type": "application/json"},
                json={"userCode": user_code, "secretKey": secret_key},
                timeout=10,
            )

        if response.status_code >= 400:
            raise ValueError(response.text or f"SureM token request failed ({response.status_code}).")

        payload = response.json()
        token = ((payload.get("data") or {}).get("accessToken")) if isinstance(payload, dict) else None
        expires_in = ((payload.get("data") or {}).get("expiresIn")) if isinstance(payload, dict) else None
        if not token:
            raise ValueError(payload.get("message") or "SureM token response did not include accessToken.")

        ttl = int(expires_in or 3600)
        cls._cached_token = token
        cls._token_expires_at = datetime.now(timezone.utc) + timedelta(seconds=max(ttl - 60, 60))
        return token

    @classmethod
    def reset_token_cache(cls) -> None:
        cls._cached_token = None
        cls._token_expires_at = None

    @classmethod
    def _fixed_to_number(cls) -> str:
        value = cls._env_any("SUREM_FORCE_TO_NUMBER", "SUREM_TO")
        if not value:
            raise ValueError("SUREM_FORCE_TO_NUMBER must be configured for fixed-recipient relay sends.")
        return value

    @classmethod
    def _request_phone(cls) -> str:
        value = cls._env_any("SUREM_REQ_PHONE", "SUREM_reqPhone")
        if not value:
            raise ValueError("SUREM_REQ_PHONE must be configured for SureM relay sends.")
        return value

    @staticmethod
    def _truncate_sms_text(text: str) -> str:
        return SuremMessageProvider._truncate_text(text, 90)

    @staticmethod
    def _truncate_text(text: str, limit_bytes: int) -> str:
        encoded = (text or "").encode("utf-8")
        if len(encoded) <= limit_bytes:
            return text or ""

        current = bytearray()
        for char in text or "":
            char_bytes = char.encode("utf-8")
            if len(current) + len(char_bytes) > limit_bytes:
                break
            current.extend(char_bytes)
        return current.decode("utf-8", errors="ignore")

    @classmethod
    def _read_attachment_bytes(cls, payload: MessageDispatchPayload) -> tuple[bytes, str]:
        if payload.attachment_path and Path(payload.attachment_path).exists():
            path = Path(payload.attachment_path)
            return path.read_bytes(), path.name

        source = payload.attachment_path or payload.image_url or ""
        if source.startswith("/static/"):
            local_path = Path("development/web/app/static") / source.removeprefix("/static/")
            return local_path.read_bytes(), local_path.name

        raise ValueError("SureM MMS image source could not be resolved.")

    @classmethod
    def _upload_image(cls, token: str, payload: MessageDispatchPayload) -> str:
        if payload.attachment_provider_key:
            return payload.attachment_provider_key

        file_bytes, filename = cls._read_attachment_bytes(payload)
        if len(file_bytes) > 500 * 1024:
            raise ValueError("SureM MMS images must be 500KB or smaller.")
        if not filename.lower().endswith((".jpg", ".jpeg")):
            raise ValueError("SureM MMS images must be JPG.")

        with httpx.Client() as client:
            response = client.post(
                cls._env_any("SUREM_IMAGE_URL") or cls.IMAGE_URL,
                headers={"Authorization": f"Bearer {token}"},
                files={"image1": (filename, file_bytes, "image/jpeg")},
                timeout=20,
            )

        if response.status_code >= 400:
            raise ValueError(response.text or f"SureM image upload failed ({response.status_code}).")

        payload_json = response.json()
        image_key = ((payload_json.get("data") or {}).get("imageKey")) if isinstance(payload_json, dict) else None
        if not image_key:
            raise ValueError(payload_json.get("message") or "SureM image upload did not return imageKey.")
        return image_key

    def send(self, db: Any, payload: MessageDispatchPayload) -> Dict[str, Any]:
        token = self.get_access_token()
        record_type = (payload.record_type or "SMS").upper()
        endpoint = self._env_any("SUREM_SMS_URL") or self.SMS_URL
        outbound = {
            "to": self._fixed_to_number(),
            "reqPhone": self._request_phone(),
        }

        if record_type == "SMS":
            outbound["text"] = self._truncate_sms_text(payload.content or "")
        else:
            endpoint = self._env_any("SUREM_MMS_URL", "SUREM_SMS_MMS_URL") or self.MMS_URL
            outbound["text"] = self._truncate_text(payload.content or "", 2000)
            if payload.subject:
                outbound["subject"] = payload.subject[:30]
            if record_type == "MMS":
                outbound["imageKey"] = self._upload_image(token, payload)

        with httpx.Client() as client:
            response = client.post(
                endpoint,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {token}",
                },
                json=outbound,
                timeout=20,
            )

        if response.status_code >= 400:
            return {
                "status": "error",
                "provider": self.provider_name,
                "message": response.text or f"SureM SMS send failed ({response.status_code}).",
            }

        payload_json = response.json()
        response_code = payload_json.get("code") if isinstance(payload_json, dict) else None
        response_message = payload_json.get("message") if isinstance(payload_json, dict) else None
        return {
            "status": "success" if response_code in {"200", "A0000", "SUCCESS", None} else "error",
            "provider": self.provider_name,
            "code": response_code or "SUREM_OK",
            "message": response_message or "SureM accepted the SMS request.",
        }
