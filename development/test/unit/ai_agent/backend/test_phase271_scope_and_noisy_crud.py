from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from ai_agent.ui.backend.service import AiAgentService


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "query",
    [
        "what is the capital of france",
        "tell me a joke",
        "how is the weather today",
    ],
)
async def test_out_of_scope_natural_language_is_refused_without_llm(query):
    with patch.object(AiAgentService, "_call_multi_llm_ensemble", new_callable=AsyncMock) as llm_call:
        response = await AiAgentService.process_query(
            db=object(),
            user_query=query,
            conversation_id="phase271-out-of-scope",
        )

    assert response["intent"] == "CHAT"
    assert "D5 CRM" in response["text"]
    llm_call.assert_not_called()


@pytest.mark.asyncio
async def test_typo_create_contact_still_flows_to_crud_without_llm():
    contact = SimpleNamespace(
        id="CONTACT271C",
        first_name="Ada",
        last_name="Kim",
        email="ada@example.com",
        phone="01012341234",
        status="New",
        gender=None,
        website=None,
        tier="Gold",
        description=None,
    )

    with patch("web.backend.app.services.contact_service.ContactService.create_contact", return_value=contact), patch.object(
        AiAgentService, "_call_multi_llm_ensemble", new_callable=AsyncMock
    ) as llm_call:
        response = await AiAgentService.process_query(
            db=object(),
            user_query="create cntact first name Ada last name Kim status New email ada@example.com",
            conversation_id="phase271-contact-typo",
        )

    assert response["intent"] == "OPEN_RECORD"
    assert response["object_type"] == "contact"
    llm_call.assert_not_called()


@pytest.mark.asyncio
async def test_korean_dialect_create_contact_still_flows_to_crud_without_llm():
    contact = SimpleNamespace(
        id="CONTACT271K",
        first_name="민수",
        last_name="김",
        email=None,
        phone=None,
        status="New",
        gender=None,
        website=None,
        tier="Bronze",
        description=None,
    )

    with patch("web.backend.app.services.contact_service.ContactService.create_contact", return_value=contact), patch.object(
        AiAgentService, "_call_multi_llm_ensemble", new_callable=AsyncMock
    ) as llm_call:
        response = await AiAgentService.process_query(
            db=object(),
            user_query="연락처 하나 맹글어줘 last name 김 status New",
            conversation_id="phase271-contact-dialect",
        )

    assert response["intent"] == "OPEN_RECORD"
    assert response["object_type"] == "contact"
    llm_call.assert_not_called()


@pytest.mark.asyncio
async def test_dialect_update_opportunity_still_flows_to_crud_without_llm():
    opportunity = SimpleNamespace(
        id="OPP271D",
        name="Fleet Renewal",
        amount=90000,
        stage="Closed Won",
        status="Open",
        probability=80,
        contact=None,
        brand=None,
        model=None,
        product=None,
        asset=None,
        temperature="Warm",
    )

    with patch("web.backend.app.services.opportunity_service.OpportunityService.update_opportunity", return_value=opportunity), patch(
        "web.backend.app.services.opportunity_service.OpportunityService.get_opportunity",
        return_value=opportunity,
    ), patch.object(AiAgentService, "_call_multi_llm_ensemble", new_callable=AsyncMock) as llm_call:
        response = await AiAgentService.process_query(
            db=object(),
            user_query="기회 OPP271D stage Closed Won 바까줘",
            conversation_id="phase271-opportunity-dialect",
        )

    assert response["intent"] == "OPEN_RECORD"
    assert response["object_type"] == "opportunity"
    llm_call.assert_not_called()


@pytest.mark.asyncio
async def test_typo_update_asset_still_flows_to_crud_without_llm():
    asset = SimpleNamespace(
        id="ASSET271T",
        name="Demo Asset",
        vin="KMH271VIN",
        status="Active",
        price=25000,
        product=None,
        brand=None,
        model=None,
        contact=None,
    )

    with patch("web.backend.app.services.asset_service.AssetService.update_asset", return_value=asset), patch(
        "web.backend.app.services.asset_service.AssetService.get_asset",
        return_value=asset,
    ), patch.object(AiAgentService, "_call_multi_llm_ensemble", new_callable=AsyncMock) as llm_call:
        response = await AiAgentService.process_query(
            db=object(),
            user_query="update aseet ASSET271T status Active",
            conversation_id="phase271-asset-typo",
        )

    assert response["intent"] == "OPEN_RECORD"
    assert response["object_type"] == "asset"
    llm_call.assert_not_called()


@pytest.mark.asyncio
async def test_typo_manage_brand_still_flows_to_crud_without_llm():
    brand = SimpleNamespace(
        id="BRAND271T",
        name="Genesis",
        record_type="Brand",
        description="Luxury",
    )

    with patch("web.backend.app.services.vehicle_spec_service.VehicleSpecService.get_vehicle_spec", return_value=brand), patch.object(
        AiAgentService, "_call_multi_llm_ensemble", new_callable=AsyncMock
    ) as llm_call:
        response = await AiAgentService.process_query(
            db=object(),
            user_query="show brnad BRAND271T",
            conversation_id="phase271-brand-typo",
        )

    assert response["intent"] == "OPEN_RECORD"
    assert response["object_type"] == "brand"
    llm_call.assert_not_called()


@pytest.mark.asyncio
async def test_typo_create_product_still_flows_to_crud_without_llm():
    product = SimpleNamespace(
        id="PROD271T",
        name="Premium Plan",
        brand=None,
        model=None,
        category="SUV",
        base_price=55000,
        description="Launch product",
    )

    with patch("web.backend.app.services.product_service.ProductService.create_product", return_value=product), patch.object(
        AiAgentService, "_call_multi_llm_ensemble", new_callable=AsyncMock
    ) as llm_call:
        response = await AiAgentService.process_query(
            db=object(),
            user_query="create prodcut name Premium Plan base price 55000 category SUV",
            conversation_id="phase271-product-typo",
        )

    assert response["intent"] == "OPEN_RECORD"
    assert response["object_type"] == "product"
    llm_call.assert_not_called()
