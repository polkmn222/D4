from unittest.mock import MagicMock, patch

from web.message.backend.services.message_providers.base import MessageDispatchPayload
from web.message.backend.services.message_providers.surem_provider import SuremMessageProvider


def test_surem_provider_requires_credentials_for_token():
    SuremMessageProvider.reset_token_cache()
    with patch.dict("os.environ", {}, clear=True):
        try:
            SuremMessageProvider.get_access_token(force_refresh=True)
        except ValueError as exc:
            assert "SUREM_USER_CODE and SUREM_SECRET_KEY" in str(exc)
        else:
            raise AssertionError("Expected missing SureM credential error.")


def test_surem_provider_fetches_and_caches_token():
    SuremMessageProvider.reset_token_cache()
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "code": "200",
        "data": {
            "accessToken": "surem-token",
            "tokenType": "Bearer",
            "expiresIn": 3600,
        },
    }
    mock_client = MagicMock()
    mock_client.__enter__.return_value = mock_client
    mock_client.post.return_value = mock_response

    with patch.dict(
        "os.environ",
        {"SUREM_USER_CODE": "demo-user", "SUREM_SECRET_KEY": "demo-secret"},
        clear=False,
    ), patch("web.message.backend.services.message_providers.surem_provider.httpx.Client", return_value=mock_client):
        first = SuremMessageProvider.get_access_token(force_refresh=True)
        second = SuremMessageProvider.get_access_token(force_refresh=False)

    assert first == "surem-token"
    assert second == "surem-token"
    assert mock_client.post.call_count == 1
    _, kwargs = mock_client.post.call_args
    assert kwargs["json"]["userCode"] == "demo-user"
    assert kwargs["json"]["secretKey"] == "demo-secret"


def test_surem_provider_sends_sms_with_fixed_numbers():
    SuremMessageProvider.reset_token_cache()
    token_response = MagicMock()
    token_response.status_code = 200
    token_response.json.return_value = {
        "code": "200",
        "data": {
            "accessToken": "surem-token",
            "tokenType": "Bearer",
            "expiresIn": 3600,
        },
    }
    send_response = MagicMock()
    send_response.status_code = 200
    send_response.json.return_value = {
        "code": "200",
        "message": "accepted",
    }
    mock_client = MagicMock()
    mock_client.__enter__.return_value = mock_client
    mock_client.post.side_effect = [token_response, send_response]

    with patch.dict(
        "os.environ",
        {
            "SUREM_USER_CODE": "demo-user",
            "SUREM_SECRET_KEY": "demo-secret",
            "SUREM_REQ_PHONE": "15884640",
            "SUREM_FORCE_TO_NUMBER": "01000000000",
        },
        clear=False,
    ), patch("web.message.backend.services.message_providers.surem_provider.httpx.Client", return_value=mock_client):
        result = SuremMessageProvider().send(
            None,
            payload=MessageDispatchPayload(contact_id="C1", record_type="SMS", content="테스트 메시지"),
        )

    assert result["status"] == "success"
    assert result["provider"] == "surem"
    assert result["message"] == "accepted"
    assert mock_client.post.call_count == 2
    _, kwargs = mock_client.post.call_args
    assert kwargs["headers"]["Authorization"] == "Bearer surem-token"
    assert kwargs["json"]["to"] == "01000000000"
    assert kwargs["json"]["reqPhone"] == "15884640"


def test_surem_provider_truncates_sms_to_ninety_bytes():
    text = "가" * 100
    truncated = SuremMessageProvider._truncate_sms_text(text)
    assert len(truncated.encode("utf-8")) <= 90
    assert truncated


def test_surem_provider_sends_lms_via_mms_endpoint_without_image_key():
    SuremMessageProvider.reset_token_cache()
    token_response = MagicMock()
    token_response.status_code = 200
    token_response.json.return_value = {
        "code": "200",
        "data": {"accessToken": "surem-token", "tokenType": "Bearer", "expiresIn": 3600},
    }
    lms_response = MagicMock()
    lms_response.status_code = 200
    lms_response.json.return_value = {"code": "A0000", "message": "accepted"}
    mock_client = MagicMock()
    mock_client.__enter__.return_value = mock_client
    mock_client.post.side_effect = [token_response, lms_response]

    with patch.dict(
        "os.environ",
        {
            "SUREM_USER_CODE": "demo-user",
            "SUREM_SECRET_KEY": "demo-secret",
            "SUREM_REQ_PHONE": "15884640",
            "SUREM_FORCE_TO_NUMBER": "01000000000",
        },
        clear=False,
    ), patch("web.message.backend.services.message_providers.surem_provider.httpx.Client", return_value=mock_client):
        result = SuremMessageProvider().send(
            None,
            payload=MessageDispatchPayload(contact_id="C1", record_type="LMS", content="긴 메시지", subject="제목"),
        )

    assert result["status"] == "success"
    _, kwargs = mock_client.post.call_args
    assert kwargs["json"]["to"] == "01000000000"
    assert kwargs["json"]["reqPhone"] == "15884640"
    assert kwargs["json"]["subject"] == "제목"
    assert "imageKey" not in kwargs["json"]


def test_surem_provider_uploads_image_and_sends_mms():
    SuremMessageProvider.reset_token_cache()
    token_response = MagicMock()
    token_response.status_code = 200
    token_response.json.return_value = {
        "code": "200",
        "data": {"accessToken": "surem-token", "tokenType": "Bearer", "expiresIn": 3600},
    }
    upload_response = MagicMock()
    upload_response.status_code = 200
    upload_response.json.return_value = {"code": "200", "data": {"imageKey": "IMAGEKEY123"}}
    mms_response = MagicMock()
    mms_response.status_code = 200
    mms_response.json.return_value = {"code": "A0000", "message": "accepted"}
    mock_client = MagicMock()
    mock_client.__enter__.return_value = mock_client
    mock_client.post.side_effect = [token_response, upload_response, mms_response]

    with patch.dict(
        "os.environ",
        {
            "SUREM_USER_CODE": "demo-user",
            "SUREM_SECRET_KEY": "demo-secret",
            "SUREM_REQ_PHONE": "15884640",
            "SUREM_FORCE_TO_NUMBER": "01000000000",
        },
        clear=False,
    ), patch("web.message.backend.services.message_providers.surem_provider.httpx.Client", return_value=mock_client), patch.object(
        SuremMessageProvider,
        "_read_attachment_bytes",
        return_value=(b"jpg-bytes", "test.jpg"),
    ):
        result = SuremMessageProvider().send(
            None,
            payload=MessageDispatchPayload(contact_id="C1", record_type="MMS", content="mms body", subject="mms", attachment_path="/tmp/test.jpg"),
        )

    assert result["status"] == "success"
    _, kwargs = mock_client.post.call_args
    assert kwargs["json"]["imageKey"] == "IMAGEKEY123"
