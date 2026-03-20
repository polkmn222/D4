import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from ai_agent.backend.ai_service import AIService

@pytest.mark.asyncio
async def test_ai_summary_generation_mock():
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "choices": [{"message": {"content": "This is a mock summary."}}]
    }
    
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_response
        summary = await AIService.generate_summary("Test customer who likes AI.")
        assert "mock summary" in summary.lower()

@pytest.mark.asyncio
async def test_ai_summary_empty_description():
    summary = await AIService.generate_summary("")
    assert summary == ""
