from unittest.mock import patch

import pytest

from ai_agent.ui.backend.service import AiAgentService


@pytest.mark.asyncio
async def test_create_product_opens_fast_form_without_llm():
    with patch.object(AiAgentService, "_call_multi_llm_ensemble") as llm_call:
        response = await AiAgentService.process_query(
            db=None,
            user_query="create product Premium Plan",
            conversation_id="phase231-create-product",
            language_preference="eng",
        )

    assert response["intent"] == "OPEN_FORM"
    assert response["object_type"] == "product"
    assert response["form_url"] == "/products/new-modal"
    llm_call.assert_not_called()


@pytest.mark.asyncio
async def test_create_brand_opens_fast_form_without_llm():
    with patch.object(AiAgentService, "_call_multi_llm_ensemble") as llm_call:
        response = await AiAgentService.process_query(
            db=None,
            user_query="create brand Genesis",
            conversation_id="phase231-create-brand",
            language_preference="eng",
        )

    assert response["intent"] == "OPEN_FORM"
    assert response["object_type"] == "brand"
    assert response["form_url"] == "/vehicle_specifications/new-modal?type=Brand"
    llm_call.assert_not_called()


@pytest.mark.asyncio
async def test_create_message_template_opens_fast_form_without_llm():
    with patch.object(AiAgentService, "_call_multi_llm_ensemble") as llm_call:
        response = await AiAgentService.process_query(
            db=None,
            user_query="create message template",
            conversation_id="phase231-create-template",
            language_preference="eng",
        )

    assert response["intent"] == "OPEN_FORM"
    assert response["object_type"] == "message_template"
    assert response["form_url"] == "/message_templates/new-modal"
    llm_call.assert_not_called()
