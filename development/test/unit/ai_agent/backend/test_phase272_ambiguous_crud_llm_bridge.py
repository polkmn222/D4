from unittest.mock import AsyncMock, patch

import pytest

from ai_agent.llm.backend.conversation_context import ConversationContextStore
from ai_agent.ui.backend.service import AiAgentService


@pytest.mark.asyncio
async def test_non_d5_sentence_with_generic_change_is_still_refused_without_llm():
    with patch.object(AiAgentService, "_call_multi_llm_ensemble", new_callable=AsyncMock) as llm_call:
        response = await AiAgentService.process_query(
            db=object(),
            user_query="change the weather tomorrow",
            conversation_id="phase272-non-d5-change",
        )

    assert response["intent"] == "CHAT"
    assert "D5 CRM" in response["text"]
    llm_call.assert_not_called()


@pytest.mark.asyncio
async def test_ambiguous_follow_up_manage_request_can_use_llm_with_last_created_context():
    conv_id = "phase272-last-created-manage"
    ConversationContextStore.clear(conv_id)
    ConversationContextStore.remember_created(conv_id, "contact", "CONTACT272A")

    execute_intent = AsyncMock(side_effect=lambda _db, agent_output, _query, **_kwargs: agent_output)

    with patch.object(
        AiAgentService,
        "_call_multi_llm_ensemble",
        return_value={
            "intent": "MANAGE",
            "action": "manage",
            "context_reference": {"kind": "last_created", "object_type": "contact"},
            "confidence": 0.9,
        },
    ) as llm_call, patch.object(AiAgentService, "_execute_intent", execute_intent):
        response = await AiAgentService.process_query(
            db=object(),
            user_query="can u pull the one i just added",
            conversation_id=conv_id,
        )

    assert response["intent"] == "MANAGE"
    assert response["object_type"] == "contact"
    assert response["record_id"] == "CONTACT272A"
    llm_call.assert_awaited_once()
    execute_intent.assert_awaited_once()


@pytest.mark.asyncio
async def test_ambiguous_follow_up_update_request_can_use_llm_with_context_and_fields():
    conv_id = "phase272-last-record-update"
    ConversationContextStore.clear(conv_id)
    ConversationContextStore.remember_object(conv_id, "contact", "MANAGE", "CONTACT272B")

    execute_intent = AsyncMock(side_effect=lambda _db, agent_output, _query, **_kwargs: agent_output)

    with patch.object(
        AiAgentService,
        "_call_multi_llm_ensemble",
        return_value={
            "intent": "UPDATE",
            "action": "update",
            "context_reference": {"kind": "last_record", "object_type": "contact"},
            "fields_to_update": {"status": "Qualified"},
            "confidence": 0.88,
        },
    ) as llm_call, patch.object(AiAgentService, "_execute_intent", execute_intent):
        response = await AiAgentService.process_query(
            db=object(),
            user_query="set it to qualified",
            conversation_id=conv_id,
        )

    assert response["intent"] == "UPDATE"
    assert response["object_type"] == "contact"
    assert response["record_id"] == "CONTACT272B"
    assert response["data"] == {"status": "Qualified"}
    llm_call.assert_awaited_once()
    execute_intent.assert_awaited_once()


@pytest.mark.asyncio
async def test_ambiguous_follow_up_rename_request_can_use_llm_with_last_record_context():
    conv_id = "phase272-last-record-rename"
    ConversationContextStore.clear(conv_id)
    ConversationContextStore.remember_object(conv_id, "product", "MANAGE", "PROD272B")

    execute_intent = AsyncMock(side_effect=lambda _db, agent_output, _query, **_kwargs: agent_output)

    with patch.object(
        AiAgentService,
        "_call_multi_llm_ensemble",
        return_value={
            "intent": "UPDATE",
            "action": "update",
            "object_type": "product",
            "context_reference": {"kind": "last_record", "object_type": "product"},
            "fields_to_update": {"name": "VIP Fleet"},
            "confidence": 0.91,
        },
    ) as llm_call, patch.object(AiAgentService, "_execute_intent", execute_intent):
        response = await AiAgentService.process_query(
            db=object(),
            user_query="rename it to VIP Fleet",
            conversation_id=conv_id,
        )

    assert response["intent"] == "UPDATE"
    assert response["object_type"] == "product"
    assert response["record_id"] == "PROD272B"
    assert response["data"] == {"name": "VIP Fleet"}
    llm_call.assert_awaited_once()
    execute_intent.assert_awaited_once()


@pytest.mark.asyncio
async def test_ambiguous_crud_without_safe_target_uses_llm_then_returns_clarification():
    conv_id = "phase272-unsafe-update"
    ConversationContextStore.clear(conv_id)

    execute_intent = AsyncMock(side_effect=lambda _db, agent_output, _query, **_kwargs: agent_output)

    with patch.object(
        AiAgentService,
        "_call_multi_llm_ensemble",
        return_value={
            "intent": "UPDATE",
            "action": "update",
            "object_type": "contact",
            "fields_to_update": {"status": "Qualified"},
            "context_reference": {"kind": "that_one"},
            "confidence": 0.9,
        },
    ) as llm_call, patch.object(AiAgentService, "_execute_intent", execute_intent):
        response = await AiAgentService.process_query(
            db=object(),
            user_query="set that one to qualified",
            conversation_id=conv_id,
    )

    assert response["intent"] == "CHAT"
    assert "exact contact record" in response["text"]
    llm_call.assert_awaited_once()
    execute_intent.assert_awaited_once()
