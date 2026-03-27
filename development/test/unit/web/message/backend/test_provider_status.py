from unittest.mock import patch

from web.message.backend.services.message_providers.factory import MessageProviderFactory
from web.message.backend.services.messaging_service import MessagingService


def test_provider_status_warns_for_solapi_on_vercel():
    with patch.dict(
        "os.environ",
        {
            "MESSAGE_PROVIDER": "solapi",
            "VERCEL": "1",
            "SOLAPI_API_KEY": "key",
            "SOLAPI_API_SECRET": "secret",
            "SOLAPI_SENDER_NUMBER": "01012341234",
        },
        clear=False,
    ):
        status = MessageProviderFactory.get_provider_status()

    assert status["provider"] == "solapi"
    assert status["environment"]["vercel"] is True
    assert status["solapi"]["allow_on_vercel_override"] is False
    assert any("dynamic outbound IPs" in warning for warning in status["warnings"])


def test_provider_status_marks_slack_as_dev_test_only():
    with patch.dict(
        "os.environ",
        {
            "MESSAGE_PROVIDER": "slack",
            "SLACK_MESSAGE_WEBHOOK_URL": "https://hooks.slack.com/services/test",
        },
        clear=False,
    ):
        status = MessageProviderFactory.get_provider_status()

    assert status["provider"] == "slack"
    assert status["slack"]["configured"] is True
    assert any("dev/test verification only" in warning for warning in status["warnings"])


def test_provider_status_reports_relay_configuration():
    with patch.dict(
        "os.environ",
        {
            "MESSAGE_PROVIDER": "relay",
            "RELAY_MESSAGE_ENDPOINT": "https://relay.example.com/messaging/relay-dispatch",
            "RELAY_MESSAGE_TOKEN": "secret",
        },
        clear=False,
    ):
        status = MessageProviderFactory.get_provider_status()

    assert status["provider"] == "relay"
    assert status["relay"]["endpoint_configured"] is True
    assert status["relay"]["token_configured"] is True
    assert any("separate runtime" in warning for warning in status["warnings"])


def test_provider_status_defaults_to_mock():
    with patch.dict("os.environ", {}, clear=True):
        status = MessageProviderFactory.get_provider_status()

    assert status["provider"] == "mock"
    assert any("does not contact any external delivery service" in warning for warning in status["warnings"])


def test_solapi_is_blocked_on_vercel_by_default():
    with patch.dict(
        "os.environ",
        {
            "MESSAGE_PROVIDER": "solapi",
            "VERCEL": "1",
        },
        clear=False,
    ):
        try:
            MessagingService._enforce_provider_runtime_guard()
        except ValueError as exc:
            assert "blocked on Vercel by default" in str(exc)
        else:
            raise AssertionError("Expected Vercel solapi guard to raise.")


def test_solapi_can_be_overridden_on_vercel():
    with patch.dict(
        "os.environ",
        {
            "MESSAGE_PROVIDER": "solapi",
            "VERCEL": "1",
            "ALLOW_SOLAPI_ON_VERCEL": "true",
        },
        clear=False,
    ):
        MessagingService._enforce_provider_runtime_guard()
