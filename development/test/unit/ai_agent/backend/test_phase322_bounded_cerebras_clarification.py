from unittest.mock import AsyncMock, patch

import pytest

from ai_agent.ui.backend.service import AiAgentService


@pytest.mark.asyncio
async def test_can_you_search_for_lead_uses_unwrapped_deterministic_query_without_llm():
    expected = {
        "results": [{"id": "LEAD322A", "display_name": "Ada Kim"}],
        "sql": "SELECT * FROM leads",
        "pagination": {"page": 1, "per_page": 30, "total": 1, "total_pages": 1, "object_type": "lead"},
    }

    with patch.object(AiAgentService, "_execute_paginated_query", return_value=expected), patch.object(
        AiAgentService, "_call_multi_llm_ensemble", new_callable=AsyncMock
    ) as llm_call:
        response = await AiAgentService.process_query(
            db=None,
            user_query="Can you Search for Lead?",
            conversation_id="phase322-search-lead",
        )

    assert response["intent"] == "QUERY"
    assert response["object_type"] == "lead"
    llm_call.assert_not_called()


@pytest.mark.asyncio
async def test_can_you_find_lead_named_john_uses_unwrapped_query_without_llm():
    expected = {
        "results": [{"id": "LEAD322B", "display_name": "John Kim"}],
        "sql": "SELECT * FROM leads",
        "pagination": {"page": 1, "per_page": 30, "total": 1, "total_pages": 1, "object_type": "lead"},
    }

    with patch.object(AiAgentService, "_execute_paginated_query", return_value=expected), patch.object(
        AiAgentService, "_call_multi_llm_ensemble", new_callable=AsyncMock
    ) as llm_call:
        response = await AiAgentService.process_query(
            db=None,
            user_query="Can you Find Lead named John?",
            conversation_id="phase323-find-lead-john",
        )

    assert response["intent"] == "QUERY"
    assert response["object_type"] == "lead"
    llm_call.assert_not_called()


@pytest.mark.asyncio
async def test_show_lead_summary_uses_bounded_cerebras_clarification_without_full_ensemble():
    cerebras_response = {
        "intent": "CHAT",
        "text": "Do you want me to search leads, show recent leads, or open a lead by name?",
        "options": [
            {"label": "Search Leads", "value": "search lead"},
            {"label": "Recent Leads", "value": "show recent leads"},
        ],
        "score": 0.93,
    }

    with patch("ai_agent.ui.backend.service.CEREBRAS_API_KEY", "test-key"), patch.object(
        AiAgentService, "_call_cerebras", new_callable=AsyncMock, return_value=cerebras_response
    ) as cerebras_call, patch.object(
        AiAgentService, "_call_multi_llm_ensemble", new_callable=AsyncMock
    ) as llm_call:
        response = await AiAgentService.process_query(
            db=None,
            user_query="Show Lead summary",
            conversation_id="phase322-lead-summary",
        )

    assert response["intent"] == "CHAT"
    assert "search leads" in response["text"].lower()
    cerebras_call.assert_awaited_once()
    llm_call.assert_not_called()


@pytest.mark.asyncio
async def test_show_lead_summary_uses_local_fallback_when_cerebras_response_is_invalid():
    with patch("ai_agent.ui.backend.service.CEREBRAS_API_KEY", "test-key"), patch.object(
        AiAgentService, "_call_cerebras", new_callable=AsyncMock, return_value={"intent": "QUERY"}
    ) as cerebras_call, patch.object(
        AiAgentService, "_call_multi_llm_ensemble", new_callable=AsyncMock
    ) as llm_call:
        response = await AiAgentService.process_query(
            db=None,
            user_query="Show Lead summary",
            conversation_id="phase322-lead-summary-fallback",
        )

    assert response["intent"] == "CHAT"
    assert "sounds like a Lead information request".lower() in response["text"].lower()
    assert response["object_type"] == "lead"
    cerebras_call.assert_awaited_once()
    llm_call.assert_not_called()


@pytest.mark.asyncio
async def test_update_lead_status_uses_bounded_update_clarification_without_full_ensemble():
    cerebras_response = {
        "intent": "CHAT",
        "text": "Which lead should I update? I can show recent leads, search leads, or edit a lead by ID.",
        "options": [
            {"label": "Recent Leads", "value": "show recent leads"},
            {"label": "Search Leads", "value": "search lead"},
            {"label": "Edit By ID", "value": "edit lead [ID]"},
        ],
        "score": 0.94,
    }

    with patch("ai_agent.ui.backend.service.CEREBRAS_API_KEY", "test-key"), patch.object(
        AiAgentService, "_call_cerebras", new_callable=AsyncMock, return_value=cerebras_response
    ) as cerebras_call, patch.object(
        AiAgentService, "_call_multi_llm_ensemble", new_callable=AsyncMock
    ) as llm_call:
        response = await AiAgentService.process_query(
            db=None,
            user_query="Can you Update Lead status?",
            conversation_id="phase323-update-lead-status",
        )

    assert response["intent"] == "CHAT"
    assert "which lead" in response["text"].lower()
    assert response["object_type"] == "lead"
    cerebras_call.assert_awaited_once()
    llm_call.assert_not_called()


@pytest.mark.asyncio
async def test_update_lead_status_uses_local_fallback_when_bounded_update_response_is_invalid():
    with patch("ai_agent.ui.backend.service.CEREBRAS_API_KEY", "test-key"), patch.object(
        AiAgentService, "_call_cerebras", new_callable=AsyncMock, return_value={"intent": "UPDATE"}
    ) as cerebras_call, patch.object(
        AiAgentService, "_call_multi_llm_ensemble", new_callable=AsyncMock
    ) as llm_call:
        response = await AiAgentService.process_query(
            db=None,
            user_query="Update Lead status",
            conversation_id="phase323-update-lead-status-fallback",
        )

    assert response["intent"] == "CHAT"
    assert "sounds like a lead update request" in response["text"].lower()
    assert "which lead should i update" in response["text"].lower()
    assert response["object_type"] == "lead"
    cerebras_call.assert_awaited_once()
    llm_call.assert_not_called()


@pytest.mark.asyncio
async def test_is_there_any_lead_for_tesla_uses_deterministic_query_without_llm():
    expected = {
        "results": [{"id": "LEAD324A", "display_name": "Tesla Prospect"}],
        "sql": "SELECT * FROM leads",
        "pagination": {"page": 1, "per_page": 30, "total": 1, "total_pages": 1, "object_type": "lead"},
    }

    with patch.object(AiAgentService, "_execute_paginated_query", return_value=expected), patch.object(
        AiAgentService, "_call_multi_llm_ensemble", new_callable=AsyncMock
    ) as llm_call:
        response = await AiAgentService.process_query(
            db=None,
            user_query="Is there any Lead for Tesla?",
            conversation_id="phase324-existence-query",
        )

    assert response["intent"] == "QUERY"
    assert response["object_type"] == "lead"
    assert response["data"]["search_term"] == "tesla"
    llm_call.assert_not_called()


@pytest.mark.asyncio
async def test_guide_me_through_lead_creation_returns_local_guidance_without_llm():
    with patch.object(
        AiAgentService, "_call_multi_llm_ensemble", new_callable=AsyncMock
    ) as llm_call:
        response = await AiAgentService.process_query(
            db=None,
            user_query="Guide me through Lead creation",
            conversation_id="phase324-lead-guidance",
        )

    assert response["intent"] == "CHAT"
    assert response["object_type"] == "lead"
    assert "last name and status" in response["text"].lower()
    llm_call.assert_not_called()


@pytest.mark.asyncio
async def test_which_lead_is_hot_returns_local_guidance_without_llm():
    with patch.object(
        AiAgentService, "_call_multi_llm_ensemble", new_callable=AsyncMock
    ) as llm_call:
        response = await AiAgentService.process_query(
            db=None,
            user_query="Which Lead is hot?",
            conversation_id="phase325-hot-lead-guidance",
        )

    assert response["intent"] == "CHAT"
    assert response["object_type"] == "lead"
    assert "ranking rule" in response["text"].lower()
    llm_call.assert_not_called()


@pytest.mark.asyncio
async def test_help_with_lead_flow_returns_local_guidance_without_llm():
    with patch.object(
        AiAgentService, "_call_multi_llm_ensemble", new_callable=AsyncMock
    ) as llm_call:
        response = await AiAgentService.process_query(
            db=None,
            user_query="Help with Lead flow",
            conversation_id="phase325-flow-guidance",
        )

    assert response["intent"] == "CHAT"
    assert response["object_type"] == "lead"
    assert "help with the lead flow" in response["text"].lower()
    llm_call.assert_not_called()


@pytest.mark.asyncio
async def test_search_lead_single_hit_auto_opens_record_without_llm():
    expected = {
        "results": [{"id": "LEAD334A", "display_name": "Tesla Prospect"}],
        "sql": "SELECT * FROM leads",
        "pagination": {"page": 1, "per_page": 30, "total": 1, "total_pages": 1, "object_type": "lead"},
    }
    open_response = {"intent": "MANAGE", "object_type": "lead", "record_id": "LEAD334A", "text": "opened"}

    with patch.object(AiAgentService, "_execute_paginated_query", return_value=expected), patch.object(
        AiAgentService, "_build_phase1_open_record_response", return_value=open_response
    ) as open_builder, patch.object(
        AiAgentService, "_get_phase1_record", return_value=type("LeadStub", (), {"id": "LEAD334A"})()
    ), patch.object(
        AiAgentService, "_call_multi_llm_ensemble", new_callable=AsyncMock
    ) as llm_call:
        response = await AiAgentService.process_query(
            db=object(),
            user_query="search lead Tesla",
            conversation_id="phase334-search-lead-auto-open",
        )

    assert response["intent"] == "MANAGE"
    assert response["record_id"] == "LEAD334A"
    open_builder.assert_called_once()
    llm_call.assert_not_called()


@pytest.mark.asyncio
async def test_search_product_single_hit_auto_opens_record_without_llm():
    expected = {
        "results": [{"id": "PROD334A", "display_name": "Tesla Bundle"}],
        "sql": "SELECT * FROM products",
        "pagination": {"page": 1, "per_page": 30, "total": 1, "total_pages": 1, "object_type": "product"},
    }
    open_response = {"intent": "MANAGE", "object_type": "product", "record_id": "PROD334A", "text": "opened"}

    product_stub = type("ProductStub", (), {"id": "PROD334A", "name": "Tesla Bundle"})()
    with patch.object(AiAgentService, "_execute_paginated_query", return_value=expected), patch(
        "web.backend.app.services.product_service.ProductService.get_product", return_value=product_stub
    ), patch(
        "ai_agent.ui.backend.service.build_object_open_record_response", return_value=open_response
    ) as open_builder, patch.object(
        AiAgentService, "_build_product_chat_card", return_value={"id": "PROD334A"}
    ), patch.object(
        AiAgentService, "_call_multi_llm_ensemble", new_callable=AsyncMock
    ) as llm_call:
        response = await AiAgentService.process_query(
            db=object(),
            user_query="search product Tesla",
            conversation_id="phase334-search-product-auto-open",
        )

    assert response["intent"] == "MANAGE"
    assert response["record_id"] == "PROD334A"
    open_builder.assert_called_once()
    llm_call.assert_not_called()


@pytest.mark.asyncio
async def test_lemme_see_brand_single_hit_auto_opens_record_without_llm():
    expected = {
        "results": [{"id": "BRA339A", "display_name": "Tesla"}],
        "sql": "SELECT * FROM vehicle_specifications",
        "pagination": {"page": 1, "per_page": 30, "total": 1, "total_pages": 1, "object_type": "brand"},
    }
    open_response = {"intent": "OPEN_RECORD", "object_type": "brand", "record_id": "BRA339A", "text": "opened"}

    with patch.object(AiAgentService, "_execute_paginated_query", return_value=expected), patch(
        "web.backend.app.services.vehicle_spec_service.VehicleSpecService.get_vehicle_spec",
        return_value=type("BrandStub", (), {"id": "BRA339A", "name": "Tesla", "record_type": "Brand"})(),
    ), patch(
        "ai_agent.ui.backend.service.build_object_open_record_response",
        return_value=open_response,
    ) as open_builder, patch.object(
        AiAgentService, "_build_brand_chat_card", return_value={"id": "BRA339A"}
    ), patch.object(
        AiAgentService, "_call_multi_llm_ensemble", new_callable=AsyncMock
    ) as llm_call:
        response = await AiAgentService.process_query(
            db=object(),
            user_query="lemme see brand Tesla thread 0",
            conversation_id="phase339-lemme-see-brand-open",
        )

    assert response["intent"] == "OPEN_RECORD"
    assert response["object_type"] == "brand"
    assert response["record_id"] == "BRA339A"
    open_builder.assert_called_once()
    llm_call.assert_not_called()


@pytest.mark.asyncio
async def test_lemme_see_product_single_hit_auto_opens_record_without_llm():
    expected = {
        "results": [{"id": "PRO339A", "display_name": "Tesla Bundle"}],
        "sql": "SELECT * FROM products",
        "pagination": {"page": 1, "per_page": 30, "total": 1, "total_pages": 1, "object_type": "product"},
    }
    open_response = {"intent": "OPEN_RECORD", "object_type": "product", "record_id": "PRO339A", "text": "opened"}

    with patch.object(AiAgentService, "_execute_paginated_query", return_value=expected), patch(
        "web.backend.app.services.product_service.ProductService.get_product",
        return_value=type("ProductStub", (), {"id": "PRO339A", "name": "Tesla Bundle"})(),
    ), patch(
        "ai_agent.ui.backend.service.build_object_open_record_response",
        return_value=open_response,
    ) as open_builder, patch.object(
        AiAgentService, "_build_product_chat_card", return_value={"id": "PRO339A"}
    ), patch.object(
        AiAgentService, "_call_multi_llm_ensemble", new_callable=AsyncMock
    ) as llm_call:
        response = await AiAgentService.process_query(
            db=object(),
            user_query="lemme see product Tesla thread 0",
            conversation_id="phase339-lemme-see-product-open",
        )

    assert response["intent"] == "OPEN_RECORD"
    assert response["object_type"] == "product"
    assert response["record_id"] == "PRO339A"
    open_builder.assert_called_once()
    llm_call.assert_not_called()


@pytest.mark.asyncio
async def test_search_brnd_uses_deterministic_query_without_llm():
    expected = {
        "results": [{"id": "BRAND337A", "display_name": "Acme"}],
        "sql": "SELECT * FROM vehicle_specifications",
        "pagination": {"page": 1, "per_page": 30, "total": 2, "total_pages": 1, "object_type": "brand"},
    }

    with patch.object(AiAgentService, "_execute_paginated_query", return_value=expected), patch.object(
        AiAgentService, "_call_multi_llm_ensemble", new_callable=AsyncMock
    ) as llm_call:
        response = await AiAgentService.process_query(
            db=None,
            user_query="search brnd Acme",
            conversation_id="phase337-search-brnd",
        )

    assert response["intent"] == "QUERY"
    assert response["object_type"] == "brand"
    assert response["data"]["search_term"] == "acme"
    llm_call.assert_not_called()


@pytest.mark.asyncio
async def test_manage_brnd_alias_normalizes_to_brand_without_llm_record_guess():
    open_response = {"intent": "MANAGE", "object_type": "brand", "record_id": "BRA-338-001", "text": "opened"}

    with patch.object(
        AiAgentService, "_call_multi_llm_ensemble", new_callable=AsyncMock, return_value={"intent": "CHAT", "text": "fallback"}
    ) as llm_call, patch(
        "web.backend.app.services.vehicle_spec_service.VehicleSpecService.get_vehicle_spec",
        return_value=type("BrandStub", (), {"id": "BRA-338-001", "name": "Alias Brand", "record_type": "Brand"})(),
    ), patch(
        "ai_agent.ui.backend.service.build_object_open_record_response",
        ) as open_builder:
        open_builder.return_value = open_response
        with patch.object(AiAgentService, "_build_brand_chat_card", return_value={"id": "BRA-338-001"}):
            response = await AiAgentService.process_query(
                db=object(),
                user_query="manage brnd BRA-338-001 asap",
                conversation_id="phase338-manage-brnd-alias",
            )

    assert response["intent"] == "MANAGE"
    assert response["object_type"] == "brand"
    assert response["record_id"] == "BRA-338-001"
    open_builder.assert_called_once()
    llm_call.assert_not_awaited()


@pytest.mark.asyncio
async def test_manage_prod_alias_normalizes_to_product_without_llm_record_guess():
    open_response = {"intent": "MANAGE", "object_type": "product", "record_id": "PRO-338-001", "text": "opened"}

    with patch.object(
        AiAgentService, "_call_multi_llm_ensemble", new_callable=AsyncMock, return_value={"intent": "CHAT", "text": "fallback"}
    ) as llm_call, patch(
        "web.backend.app.services.product_service.ProductService.get_product",
        return_value=type("ProductStub", (), {"id": "PRO-338-001", "name": "Alias Product"})(),
    ), patch(
        "ai_agent.ui.backend.service.build_object_open_record_response",
        return_value=open_response,
    ) as open_builder, patch.object(
        AiAgentService, "_build_product_chat_card", return_value={"id": "PRO-338-001"}
    ):
        response = await AiAgentService.process_query(
            db=object(),
            user_query="manage prod PRO-338-001 asap",
            conversation_id="phase338-manage-prod-alias",
        )

    assert response["intent"] == "MANAGE"
    assert response["object_type"] == "product"
    assert response["record_id"] == "PRO-338-001"
    open_builder.assert_called_once()
    llm_call.assert_not_awaited()
