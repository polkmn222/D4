from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from ai_agent.ui.backend.service import AiAgentService


@pytest.mark.asyncio
async def test_save_contact_uses_deterministic_update_without_llm():
    contact = SimpleNamespace(
        id="CONTACT269S",
        first_name="Ada",
        last_name="Kim",
        email="ada@example.com",
        phone="01099998888",
        status="Qualified",
        gender=None,
        website=None,
        tier="Gold",
        description=None,
    )

    with patch("web.backend.app.services.contact_service.ContactService.update_contact", return_value=contact), patch(
        "web.backend.app.services.contact_service.ContactService.get_contact",
        return_value=contact,
    ), patch.object(AiAgentService, "_call_multi_llm_ensemble", new_callable=AsyncMock) as llm_call:
        response = await AiAgentService.process_query(
            db=object(),
            user_query="save contact CONTACT269S phone 01099998888 status Qualified",
            conversation_id="phase269-contact-save",
        )

    assert response["intent"] == "OPEN_RECORD"
    assert response["object_type"] == "contact"
    assert response["record_id"] == "CONTACT269S"
    llm_call.assert_not_called()


@pytest.mark.asyncio
async def test_save_opportunity_uses_deterministic_update_without_llm():
    opportunity = SimpleNamespace(
        id="OPP269S",
        name="Fleet Renewal",
        amount=90000,
        stage="Closed Won",
        status="Open",
        probability=90,
        contact=None,
        brand=None,
        model=None,
        product=None,
        asset=None,
        temperature="Hot",
    )

    with patch("web.backend.app.services.opportunity_service.OpportunityService.update_opportunity", return_value=opportunity), patch(
        "web.backend.app.services.opportunity_service.OpportunityService.get_opportunity",
        return_value=opportunity,
    ), patch.object(AiAgentService, "_call_multi_llm_ensemble", new_callable=AsyncMock) as llm_call:
        response = await AiAgentService.process_query(
            db=object(),
            user_query="save opportunity OPP269S stage Closed Won probability 90",
            conversation_id="phase269-opportunity-save",
        )

    assert response["intent"] == "OPEN_RECORD"
    assert response["object_type"] == "opportunity"
    assert response["record_id"] == "OPP269S"
    llm_call.assert_not_called()


@pytest.mark.asyncio
async def test_create_product_returns_open_record_without_llm():
    product = SimpleNamespace(
        id="PROD269C",
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
            user_query="create product name Premium Plan base price 55000 category SUV description Launch product",
            conversation_id="phase269-product-create",
        )

    assert response["intent"] == "OPEN_RECORD"
    assert response["object_type"] == "product"
    assert response["record_id"] == "PROD269C"
    assert response["redirect_url"] == "/products/PROD269C"
    llm_call.assert_not_called()


@pytest.mark.asyncio
async def test_update_asset_returns_open_record_without_llm():
    asset = SimpleNamespace(
        id="ASSET269U",
        name="Demo Asset",
        vin="KMH269ASSETVIN",
        status="Active",
        price=45000,
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
            user_query="update asset ASSET269U status Active price 45000",
            conversation_id="phase269-asset-update",
        )

    assert response["intent"] == "OPEN_RECORD"
    assert response["object_type"] == "asset"
    assert response["record_id"] == "ASSET269U"
    llm_call.assert_not_called()


@pytest.mark.asyncio
async def test_update_brand_returns_open_record_without_llm():
    brand = SimpleNamespace(
        id="BRAND269U",
        name="Hyundai Premium",
        record_type="Brand",
        description="Updated description",
    )

    with patch("web.backend.app.services.vehicle_spec_service.VehicleSpecService.update_vehicle_spec", return_value=brand), patch(
        "web.backend.app.services.vehicle_spec_service.VehicleSpecService.get_vehicle_spec",
        return_value=brand,
    ), patch.object(AiAgentService, "_call_multi_llm_ensemble", new_callable=AsyncMock) as llm_call:
        response = await AiAgentService.process_query(
            db=object(),
            user_query="update brand BRAND269U name Hyundai Premium description Updated description",
            conversation_id="phase269-brand-update",
        )

    assert response["intent"] == "OPEN_RECORD"
    assert response["object_type"] == "brand"
    assert response["record_id"] == "BRAND269U"
    llm_call.assert_not_called()


@pytest.mark.asyncio
async def test_create_message_template_with_fields_still_opens_form_without_llm():
    with patch.object(AiAgentService, "_call_multi_llm_ensemble", new_callable=AsyncMock) as llm_call:
        response = await AiAgentService.process_query(
            db=object(),
            user_query="create message template name Promo Blast subject Hello content Buy now",
            conversation_id="phase269-template-create",
        )

    assert response["intent"] == "OPEN_FORM"
    assert response["object_type"] == "message_template"
    assert response["form_url"] == "/message_templates/new-modal"
    llm_call.assert_not_called()


@pytest.mark.asyncio
async def test_update_message_template_opens_edit_form_without_llm():
    template = SimpleNamespace(
        id="TPL269U",
        name="Promo Blast",
        subject="Hello",
        content="Buy now",
        record_type="MMS",
        image_url="/static/uploads/message_templates/promo.jpg",
        attachment_id="ATT269U",
    )

    with patch(
        "web.message.backend.services.message_template_service.MessageTemplateService.get_template",
        return_value=template,
    ), patch.object(AiAgentService, "_call_multi_llm_ensemble", new_callable=AsyncMock) as llm_call:
        response = await AiAgentService.process_query(
            db=object(),
            user_query="update message template TPL269U subject Updated Hello",
            conversation_id="phase269-template-update",
        )

    assert response["intent"] == "OPEN_FORM"
    assert response["object_type"] == "message_template"
    assert response["record_id"] == "TPL269U"
    assert response["form_url"] == "/message_templates/new-modal?id=TPL269U"
    llm_call.assert_not_called()
