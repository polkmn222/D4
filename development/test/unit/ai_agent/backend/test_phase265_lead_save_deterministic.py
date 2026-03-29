import sys
import types
from types import SimpleNamespace
from unittest.mock import patch

import pytest
from sqlalchemy.orm import declarative_base

if "db.database" not in sys.modules:
    fake_db_database = types.ModuleType("db.database")
    fake_db_database.Base = declarative_base()
    fake_db_database.engine = None
    fake_db_database.SessionLocal = None
    fake_db_database.get_db = lambda: None
    sys.modules["db.database"] = fake_db_database

from ai_agent.ui.backend.service import AiAgentService


@pytest.mark.asyncio
async def test_create_request_with_existing_context_still_creates_lead_without_llm():
    created = SimpleNamespace(id="LEAD265C", first_name="Ada", last_name="Kim", status="New")
    context = {"last_object": "lead", "last_record_id": "LEAD-OLD", "last_intent": "MANAGE"}

    with patch.object(AiAgentService, "_call_multi_llm_ensemble") as llm_call, patch(
        "ai_agent.llm.backend.conversation_context.ConversationContextStore.get_context",
        return_value=context,
    ), patch(
        "web.backend.app.services.lead_service.LeadService.create_lead",
        return_value=created,
    ) as create_lead, patch(
        "web.backend.app.services.lead_service.LeadService.update_lead"
    ) as update_lead:
        response = await AiAgentService.process_query(
            db=None,
            user_query="create lead last name Kim status New",
            conversation_id="phase265-create-context",
        )

    assert response["intent"] == "OPEN_RECORD"
    assert response["record_id"] == "LEAD265C"
    create_lead.assert_called_once_with(None, last_name="Kim", status="New")
    update_lead.assert_not_called()
    llm_call.assert_not_called()


@pytest.mark.asyncio
async def test_save_request_with_create_fields_creates_lead_without_llm():
    created = SimpleNamespace(id="LEAD265S", first_name="Ada", last_name="Kim", status="New")
    context = {"last_object": "lead", "last_record_id": "LEAD-OLD", "last_intent": "UPDATE"}

    with patch.object(AiAgentService, "_call_multi_llm_ensemble") as llm_call, patch(
        "ai_agent.llm.backend.conversation_context.ConversationContextStore.get_context",
        return_value=context,
    ), patch(
        "web.backend.app.services.lead_service.LeadService.create_lead",
        return_value=created,
    ) as create_lead, patch(
        "web.backend.app.services.lead_service.LeadService.update_lead"
    ) as update_lead:
        response = await AiAgentService.process_query(
            db=None,
            user_query="lead save for Kim status New",
            conversation_id="phase265-save-create",
        )

    assert response["intent"] == "OPEN_RECORD"
    assert response["record_id"] == "LEAD265S"
    create_lead.assert_called_once_with(None, last_name="Kim", status="New")
    update_lead.assert_not_called()
    llm_call.assert_not_called()


@pytest.mark.asyncio
async def test_save_this_lead_uses_deterministic_edit_path_without_llm():
    lead = SimpleNamespace(
        id="LEAD265E",
        first_name="Ada",
        last_name="Kim",
        email="ada@example.com",
        phone="01012345678",
        status="Qualified",
        gender="Female",
        product=None,
        model=None,
        brand=None,
        description="Priority lead",
    )
    context = {"last_object": "lead", "last_record_id": "LEAD265E", "last_intent": "MANAGE"}

    with patch.object(AiAgentService, "_call_multi_llm_ensemble") as llm_call, patch(
        "ai_agent.llm.backend.conversation_context.ConversationContextStore.get_context",
        return_value=context,
    ), patch(
        "web.backend.app.services.lead_service.LeadService.get_lead",
        return_value=lead,
    ):
        response = await AiAgentService.process_query(
            db=None,
            user_query="please save this lead",
            conversation_id="phase265-save-current",
        )

    assert response["intent"] == "OPEN_FORM"
    assert response["record_id"] == "LEAD265E"
    llm_call.assert_not_called()
