"""
Phase 169: Lead flow consistency integration tests.
Tests use _execute_intent directly to avoid LLM non-determinism, but they exercise PostgreSQL persistence.
"""
import pytest
from unittest.mock import patch
from sqlalchemy.orm import Session

from db.models import Lead
from ai_agent.ui.backend.service import AiAgentService


pytestmark = pytest.mark.integration


@pytest.mark.asyncio
async def test_lead_create_returns_view_card(db: Session):
    agent_output = {
        "intent": "CREATE",
        "object_type": "lead",
        "data": {"first_name": "John", "last_name": "Doe", "status": "New", "email": "john@example.com"},
        "language_preference": None,
        "score": 1.0,
    }

    with patch("ai_agent.llm.backend.conversation_context.ConversationContextStore.clear_pending_create"), \
         patch("ai_agent.llm.backend.conversation_context.ConversationContextStore.remember_created"), \
         patch("ai_agent.llm.backend.conversation_context.ConversationContextStore.remember_object"):
        response = await AiAgentService._execute_intent(db, agent_output, "create lead John Doe status New email john@example.com")

    assert response["intent"] == "OPEN_RECORD"
    assert "chat_card" in response
    assert response["chat_card"]["mode"] == "view"
    assert "Doe" in response["chat_card"]["title"]

    record_id = response["chat_card"]["record_id"]
    db.query(Lead).filter(Lead.id == record_id).delete()
    db.commit()


@pytest.mark.asyncio
async def test_lead_update_returns_view_card(db: Session):
    db.query(Lead).filter(Lead.id == "TEST_FLOW_LEAD").delete()
    db.commit()

    lead = Lead(id="TEST_FLOW_LEAD", first_name="Flow", last_name="Test", status="New")
    db.add(lead)
    db.commit()

    agent_output = {
        "intent": "UPDATE",
        "object_type": "lead",
        "record_id": "TEST_FLOW_LEAD",
        "data": {"status": "Qualified"},
        "language_preference": None,
        "score": 1.0,
    }

    with patch("ai_agent.llm.backend.conversation_context.ConversationContextStore.remember_object"):
        response = await AiAgentService._execute_intent(db, agent_output, "update lead TEST_FLOW_LEAD status Qualified")

    assert response["intent"] == "OPEN_RECORD"
    assert "chat_card" in response
    assert response["chat_card"]["mode"] == "view"

    lead_to_delete = db.query(Lead).filter(Lead.id == "TEST_FLOW_LEAD").first()
    if lead_to_delete:
        db.delete(lead_to_delete)
        db.commit()
