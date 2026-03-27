import pytest
from unittest.mock import MagicMock, patch
from web.message.backend.services.messaging_service import MessagingService

def test_send_sms_auto_switch_to_lms():
    # > 90 bytes
    content = "가" * 46 
    db = MagicMock()
    contact_id = "CONT_123"
    
    with patch("web.message.backend.services.messaging_service.MessagingService._resolve_message_content", return_value=(content, None, None, None)), \
         patch("web.message.backend.services.messaging_service.MessagingService._merge_context", return_value={"name": "Test", "model": "GV80"}), \
         patch("web.message.backend.services.messaging_service.MessageProviderFactory.get_provider_by_name") as mock_factory, \
         patch("web.message.backend.services.message_service.MessageService.create_message") as mock_create:
        
        mock_provider = MagicMock()
        mock_provider.send.return_value = {"status": "success"}
        mock_provider.provider_name = "Mock"
        mock_factory.return_value = mock_provider
        
        MessagingService.send_message(db, contact_id, content=content, record_type="SMS")
        
        # Verify provider received LMS
        args, _ = mock_provider.send.call_args
        payload = args[1]
        assert payload.record_type == "LMS"

def test_send_byte_limit_2000_violation():
    content = "가" * 1001
    db = MagicMock()
    contact_id = "CONT_123"
    
    with patch("web.message.backend.services.messaging_service.MessagingService._resolve_message_content", return_value=(content, None, None, None)):
        with pytest.raises(ValueError, match="Content exceeds maximum limit"):
            MessagingService.send_message(db, contact_id, content=content)
