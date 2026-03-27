import os
from typing import Any, Dict

from .base import BaseMessageProvider
from .mock_provider import MockMessageProvider
from .relay_provider import RelayMessageProvider
from .slack_notifier import SlackMessageProvider
from .solapi_provider import SolapiMessageProvider


class MessageProviderFactory:
    @staticmethod
    def get_provider_name() -> str:
        return os.getenv("MESSAGE_PROVIDER", "mock").strip().lower() or "mock"

    @staticmethod
    def get_provider_by_name(provider_name: str) -> BaseMessageProvider:
        normalized = (provider_name or "mock").strip().lower()
        if normalized == "solapi":
            return SolapiMessageProvider()
        if normalized == "slack":
            return SlackMessageProvider()
        if normalized == "relay":
            return RelayMessageProvider()
        return MockMessageProvider()

    @staticmethod
    def get_provider() -> BaseMessageProvider:
        return MessageProviderFactory.get_provider_by_name(MessageProviderFactory.get_provider_name())

    @staticmethod
    def get_provider_status() -> Dict[str, Any]:
        provider_name = MessageProviderFactory.get_provider_name()
        is_vercel = bool(os.getenv("VERCEL"))
        render_service = os.getenv("RENDER_SERVICE_NAME", "").strip()
        return {
            "provider": provider_name,
            "environment": {
                "vercel": is_vercel,
                "render": bool(render_service),
                "render_service_name": render_service or None,
            },
            "slack": {
                "configured": bool(os.getenv("SLACK_MESSAGE_WEBHOOK_URL", "").strip()),
            },
            "relay": {
                "endpoint_configured": bool(os.getenv("RELAY_MESSAGE_ENDPOINT", "").strip()),
                "token_configured": bool(os.getenv("RELAY_MESSAGE_TOKEN", "").strip()),
                "target_provider": os.getenv("RELAY_TARGET_PROVIDER", "").strip() or "solapi",
            },
            "solapi": {
                "api_key_configured": bool(os.getenv("SOLAPI_API_KEY", "").strip()),
                "api_secret_configured": bool(os.getenv("SOLAPI_API_SECRET", "").strip()),
                "sender_number_configured": bool(os.getenv("SOLAPI_SENDER_NUMBER", "").strip()),
                "force_to_number_configured": bool(os.getenv("SOLAPI_FORCE_TO_NUMBER", "").strip()),
                "allow_on_vercel_override": bool(os.getenv("ALLOW_SOLAPI_ON_VERCEL", "").strip()),
                "allowed_ip_note": os.getenv("SOLAPI_ALLOWED_IP", "").strip() or None,
            },
            "recommendation": (
                "Use Render for real Solapi delivery when IP allowlisting matters. "
                "Use Slack only for dev/test notification verification."
            ),
            "warnings": MessageProviderFactory._build_provider_warnings(provider_name, is_vercel, bool(render_service)),
        }

    @staticmethod
    def _build_provider_warnings(provider_name: str, is_vercel: bool, is_render: bool) -> list[str]:
        warnings: list[str] = []
        if provider_name == "solapi":
            warnings.append("Solapi real delivery requires the runtime egress IP to be allowlisted in the Solapi console.")
            if is_vercel:
                warnings.append(
                    "Vercel uses dynamic outbound IPs unless Static IPs or Secure Compute is configured. "
                    "Do not rely on default Vercel egress for Solapi allowlisting."
                )
            if is_render:
                warnings.append(
                    "Render-based delivery is the preferred production path for Solapi because it is easier to manage allowlisted outbound IP requirements."
                )
        elif provider_name == "slack":
            warnings.append("Slack provider is for dev/test verification only. No carrier SMS/LMS/MMS delivery is attempted.")
        elif provider_name == "relay":
            warnings.append("Relay provider forwards delivery to a separate runtime. Keep the relay endpoint protected with RELAY_MESSAGE_TOKEN.")
        else:
            warnings.append("Mock provider does not contact any external delivery service.")
        return warnings
