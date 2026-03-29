import os
from unittest.mock import patch

from ai_agent.debug import ai_agent_debug_enabled, debug_event
from ai_agent.llm.backend.conversation_context import ConversationContextStore
from ai_agent.llm.backend.intent_preclassifier import IntentPreClassifier


def test_debug_event_logs_structured_payload_when_enabled():
    with patch.dict(os.environ, {"AI_AGENT_DEBUG": "1"}, clear=False), patch(
        "ai_agent.debug.logger.info"
    ) as info_log:
        assert ai_agent_debug_enabled() is True
        debug_event("unit.test", conversation_id="conv266", payload={"record_id": "LEAD266"})

    info_log.assert_called_once()
    logged = info_log.call_args.args[1]
    assert '"stage": "unit.test"' in logged
    assert '"conversation_id": "conv266"' in logged
    assert '"record_id": "LEAD266"' in logged


def test_debug_event_skips_logging_when_disabled():
    with patch.dict(os.environ, {"AI_AGENT_DEBUG": "0"}, clear=False), patch(
        "ai_agent.debug.logger.info"
    ) as info_log:
        debug_event("unit.disabled", conversation_id="conv266")

    info_log.assert_not_called()


def test_conversation_context_emits_debug_events_for_core_mutations():
    with patch.dict(os.environ, {"AI_AGENT_DEBUG": "1"}, clear=False), patch(
        "ai_agent.llm.backend.conversation_context.debug_event"
    ) as debug_log:
        ConversationContextStore.remember_created("conv266ctx", "lead", "LEAD266")
        ConversationContextStore.remember_object("conv266ctx", "lead", "MANAGE", record_id="LEAD266")
        ConversationContextStore.remember_selection(
            "conv266ctx",
            {"object_type": "lead", "ids": ["LEAD266"], "labels": ["Ada Kim"]},
        )
        ConversationContextStore.clear("conv266ctx")

    stages = [call.args[0] for call in debug_log.call_args_list]
    assert "context.remember_created" in stages
    assert "context.remember_object" in stages
    assert "context.remember_selection" in stages
    assert "context.clear" in stages


def test_preclassifier_emits_debug_event_for_detected_result():
    with patch.dict(os.environ, {"AI_AGENT_DEBUG": "1"}, clear=False), patch(
        "ai_agent.llm.backend.intent_preclassifier.debug_event"
    ) as debug_log:
        result = IntentPreClassifier.detect("show all leads")

    assert result is not None
    assert result["intent"] == "QUERY"
    stages = [call.args[0] for call in debug_log.call_args_list]
    assert "preclassifier.detect" in stages
