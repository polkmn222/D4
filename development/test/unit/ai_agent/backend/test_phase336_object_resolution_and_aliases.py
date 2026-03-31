from unittest.mock import AsyncMock, patch

import pytest

from ai_agent.llm.backend.intent_preclassifier import IntentPreClassifier
from ai_agent.ui.backend.service import AiAgentService


def test_detect_object_mentions_supports_short_aliases():
    assert "model" in IntentPreClassifier.detect_object_mentions("search mdl Acme")
    assert "asset" in IntentPreClassifier.detect_object_mentions("search aset Acme")
    assert "brand" in IntentPreClassifier.detect_object_mentions("search brnd Acme")
    assert "contact" in IntentPreClassifier.detect_object_mentions("search cntct Acme")
    assert "product" in IntentPreClassifier.detect_object_mentions("search prod Acme")


def test_preclassifier_treats_noun_stack_model_query_as_query():
    result = IntentPreClassifier.detect("model Tesla reddit thread style 0")

    assert result is not None
    assert result["intent"] == "QUERY"
    assert result["object_type"] == "model"
    assert result["data"]["search_term"] == "tesla reddit thread style 0"


def test_preclassifier_treats_noun_stack_brand_query_as_query():
    result = IntentPreClassifier.detect("brnd Acme reddit thread style 2")

    assert result is not None
    assert result["intent"] == "QUERY"
    assert result["object_type"] == "brand"


def test_preclassifier_treats_noun_stack_product_query_as_query():
    result = IntentPreClassifier.detect("prod Acme reddit thread style 2")

    assert result is not None
    assert result["intent"] == "QUERY"
    assert result["object_type"] == "product"


def test_preclassifier_opens_form_for_fresh_brand_form_request():
    result = IntentPreClassifier.detect("need a fresh brand form rn for Tesla")

    assert result is not None
    assert result["intent"] == "OPEN_FORM"
    assert result["object_type"] == "brand"


def test_preclassifier_opens_form_for_spin_up_product_request():
    result = IntentPreClassifier.detect("spin up a product real quick ref Tesla")

    assert result is not None
    assert result["intent"] == "OPEN_FORM"
    assert result["object_type"] == "product"


def test_preclassifier_reads_product_for_lemme_see_request():
    result = IntentPreClassifier.detect("lemme see product Tesla thread 0")

    assert result is not None
    assert result["intent"] == "QUERY"
    assert result["object_type"] == "product"
    assert result["data"]["search_term"] == "tesla thread 0"


def test_preclassifier_treats_long_brand_noisy_query_as_query():
    result = IntentPreClassifier.detect("brand Tesla reddit thread style 0")

    assert result is not None
    assert result["intent"] == "QUERY"
    assert result["object_type"] == "brand"
    assert result["data"]["search_term"] == "tesla reddit thread style 0"


def test_preclassifier_reads_open_brand_named_as_query():
    result = IntentPreClassifier.detect("open brnd named Noah Smith")

    assert result is not None
    assert result["intent"] == "QUERY"
    assert result["object_type"] == "brand"
    assert result["data"]["search_term"] == "noah smith"


def test_service_resolves_primary_object_even_when_create_payload_mentions_related_object():
    assert AiAgentService._resolve_supported_object(
        IntentPreClassifier.normalize("create model name Tesla Sport brand Tesla description reddit favorite trim 0")
    ) == "model"
    assert AiAgentService._resolve_supported_object(
        IntentPreClassifier.normalize("create Template name Tesla nurture sequence content hello from template 0 record type lead")
    ) == "message_template"


def test_send_history_resolution_does_not_hijack_message_template_queries():
    assert AiAgentService._resolve_send_history_query_request("search message template Acme") is None


@pytest.mark.asyncio
async def test_create_model_with_brand_field_uses_phase1_create_without_llm():
    created = {"intent": "CREATE", "object_type": "model", "data": {"name": "Tesla Sport", "brand": "Tesla", "description": "reddit favorite trim 0"}}

    with patch.object(AiAgentService, "_execute_intent", new_callable=AsyncMock, return_value=created) as execute_intent, patch.object(
        AiAgentService, "_call_multi_llm_ensemble", new_callable=AsyncMock
    ) as llm_call:
        response = await AiAgentService.process_query(
            db=object(),
            user_query="create model name Tesla Sport brand Tesla description reddit favorite trim 0",
            conversation_id="phase336-create-model",
        )

    assert response["intent"] == "CREATE"
    assert response["object_type"] == "model"
    execute_intent.assert_awaited_once()
    llm_call.assert_not_called()


@pytest.mark.asyncio
async def test_search_message_template_keeps_message_template_object_without_llm():
    expected = {
        "results": [{"id": "MTPL336A", "display_name": "Acme Sequence"}],
        "sql": "SELECT * FROM message_templates",
        "pagination": {"page": 1, "per_page": 30, "total": 1, "total_pages": 1, "object_type": "message_template"},
    }

    with patch.object(AiAgentService, "_execute_paginated_query", return_value=expected), patch.object(
        AiAgentService, "_call_multi_llm_ensemble", new_callable=AsyncMock
    ) as llm_call:
        response = await AiAgentService.process_query(
            db=None,
            user_query="search message template Acme",
            conversation_id="phase336-search-message-template",
        )

    assert response["intent"] == "QUERY"
    assert response["object_type"] == "message_template"
    llm_call.assert_not_called()
