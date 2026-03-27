import pytest
from unittest.mock import AsyncMock, patch
from sqlalchemy.orm import Session
from agent_gem.backend.service import AgentGemService

@pytest.mark.asyncio
async def test_process_query_chat():
    # Mock LLM response for a simple chat query
    mock_llm_response = {
        "intent": "CHAT",
        "text": "Hello! How can I help you?",
        "score": 1.0
    }
    
    with patch("agent_gem.backend.llm.AgentGemLLMService.get_intent", new=AsyncMock(return_value=mock_llm_response)):
        db = AsyncMock(spec=Session)
        response = await AgentGemService.process_query(db, "Hi")
        
        assert response["intent"] == "CHAT"
        assert "Hello" in response["text"]

@pytest.mark.asyncio
async def test_process_query_list_leads():
    # Mock LLM response for listing leads
    mock_llm_response = {
        "intent": "QUERY",
        "object_type": "lead",
        "text": "Here are your leads.",
        "score": 1.0
    }
    
    # Mock database results
    mock_db_results = [
        {"id": "lead-1", "display_name": "John Doe", "status": "New"},
        {"id": "lead-2", "display_name": "Jane Smith", "status": "Qualified"}
    ]
    
    with patch("agent_gem.backend.llm.AgentGemLLMService.get_intent", new=AsyncMock(return_value=mock_llm_response)):
        with patch("ai_agent.ui.backend.service.AiAgentService._execute_paginated_query", return_value={
            "results": mock_db_results,
            "sql": "SELECT ...",
            "pagination": {"page": 1, "per_page": 30, "total": 2, "total_pages": 1, "object_type": "lead"}
        }):
            db = AsyncMock(spec=Session)
            response = await AgentGemService.process_query(db, "Show all leads")
            
            assert response["intent"] == "QUERY"
            assert len(response["results"]) == 2
            assert response["results"][0]["display_name"] == "John Doe"

@pytest.mark.asyncio
async def test_process_query_read_lead():
    # Mock LLM response for reading a lead
    mock_llm_response = {
        "intent": "READ",
        "object_type": "lead",
        "record_id": "lead-123",
        "score": 1.0
    }
    
    # Mock Lead data
    class MockLead:
        id = "lead-123"
        first_name = "John"
        last_name = "Doe"
        status = "New"
        brand = "brand-1"
        model = "model-1"
        product = "product-1"
        phone = "010-1234-5678"
        email = "john@example.com"
        gender = "Male"
        description = "Test lead"

    with patch("agent_gem.backend.llm.AgentGemLLMService.get_intent", new=AsyncMock(return_value=mock_llm_response)):
        with patch("web.backend.app.services.lead_service.LeadService.get_lead", return_value=MockLead()):
            db = AsyncMock(spec=Session)
            response = await AgentGemService.process_query(db, "Show lead lead-123")
            
            assert response["intent"] == "READ"
            assert response["record_id"] == "lead-123"
            assert "card" in response
            assert response["card"]["title"] == "John Doe"
