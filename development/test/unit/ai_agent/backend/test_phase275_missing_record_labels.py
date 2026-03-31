from unittest.mock import patch

import pytest

from ai_agent.llm.backend.conversation_context import ConversationContextStore
from ai_agent.ui.backend.service import AiAgentService


@pytest.mark.asyncio
async def test_manage_missing_lead_prefers_recent_query_label_over_raw_id():
    conv_id = "phase275-missing-manage"
    missing_id = "00QzgNYJetmj3O5EHI"
    ConversationContextStore.clear(conv_id)
    ConversationContextStore.remember_query_results(
        conv_id,
        "lead",
        [{"id": missing_id, "display_name": "Ada Kim"}],
    )

    with patch.object(AiAgentService, "_get_phase1_record", return_value=None):
        response = await AiAgentService._execute_intent(
            db=None,
            agent_output={"intent": "MANAGE", "object_type": "lead", "record_id": missing_id},
            user_query=f"Manage lead {missing_id}",
            conversation_id=conv_id,
        )

    assert response["intent"] == "CHAT"
    assert "Ada Kim" in response["text"]
    assert missing_id not in response["text"]


@pytest.mark.asyncio
async def test_update_missing_lead_prefers_name_and_phone_over_raw_id():
    conv_id = "phase275-missing-update"
    missing_id = "00QzgNYJetmj3O5EHI"
    ConversationContextStore.clear(conv_id)

    with patch("web.backend.app.services.lead_service.LeadService.update_lead", return_value=None):
        response = await AiAgentService._execute_intent(
            db=None,
            agent_output={
                "intent": "UPDATE",
                "object_type": "lead",
                "record_id": missing_id,
                "data": {"phone": "01012341234"},
            },
            user_query=f"update lead {missing_id} first name Ada last name Kim phone 01012341234",
            conversation_id=conv_id,
        )

    assert response["intent"] == "UPDATE"
    assert "Kim" in response["text"]
    assert "01012341234" in response["text"]
    assert missing_id not in response["text"]
