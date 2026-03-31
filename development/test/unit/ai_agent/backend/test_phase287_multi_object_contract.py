from types import SimpleNamespace
from unittest.mock import patch

import pytest

from ai_agent.ui.backend.service import AiAgentService


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("object_type", "record_id", "service_patch", "record", "expected_form_url"),
    [
        (
            "product",
            "PROD287",
            "web.backend.app.services.product_service.ProductService.get_product",
            SimpleNamespace(id="PROD287", name="Touring Package", brand="BR1", model="MD1", category="SUV", base_price=55000),
            "/products/new-modal?id=PROD287",
        ),
        (
            "asset",
            "AST287",
            "web.backend.app.services.asset_service.AssetService.get_asset",
            SimpleNamespace(id="AST287", name="Demo Solace", vin="VIN287", status="Available"),
            "/assets/new-modal?id=AST287",
        ),
        (
            "brand",
            "BR287",
            "ai_agent.ui.backend.service.VehicleSpecService.get_vehicle_spec",
            SimpleNamespace(id="BR287", name="Bright Motors", record_type="Brand"),
            "/vehicle_specifications/new-modal?type=Brand&id=BR287",
        ),
        (
            "model",
            "MOD287",
            "web.backend.app.services.model_service.ModelService.get_model",
            SimpleNamespace(id="MOD287", name="Solace 2", brand="BR287"),
            "/models/new-modal?id=MOD287",
        ),
        (
            "message_template",
            "TPL287",
            "web.message.backend.services.message_template_service.MessageTemplateService.get_template",
            SimpleNamespace(id="TPL287", name="Promo Template", record_type="SMS", subject="", content="Hello"),
            "/message_templates/new-modal?id=TPL287",
        ),
    ],
)
async def test_manage_edit_for_non_phase1_objects_opens_inline_web_form(
    object_type,
    record_id,
    service_patch,
    record,
    expected_form_url,
):
    with patch(service_patch, return_value=record):
        response = await AiAgentService.process_query(
            db=None,
            user_query=f"edit {object_type} {record_id}",
            conversation_id=f"phase287-{object_type}-edit",
        )

    assert response["intent"] == "OPEN_FORM"
    assert response["object_type"] == object_type
    assert response["form_url"] == expected_form_url


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("object_type", "record", "service_patch"),
    [
        ("asset", SimpleNamespace(id="AST287D", name="Fleet Demo Asset"), "web.backend.app.services.asset_service.AssetService.get_asset"),
        ("brand", SimpleNamespace(id="BR287D", name="Aurora Motors"), "ai_agent.ui.backend.service.VehicleSpecService.get_vehicle_spec"),
        ("model", SimpleNamespace(id="MOD287D", name="Voyage 3"), "web.backend.app.services.model_service.ModelService.get_model"),
        ("message_template", SimpleNamespace(id="TPL287D", name="Spring Promo"), "web.message.backend.services.message_template_service.MessageTemplateService.get_template"),
    ],
)
async def test_delete_success_for_non_phase1_objects_prefers_human_title_not_id(object_type, record, service_patch):
    with patch(service_patch, return_value=record), patch.object(AiAgentService, "_delete_record", return_value=True):
        response = await AiAgentService._execute_intent(
            db=None,
            agent_output={"intent": "DELETE", "object_type": object_type, "record_id": record.id},
            user_query=f"delete {object_type} {record.id}",
            conversation_id=f"phase287-delete-{object_type}",
        )

    assert response["intent"] == "DELETE"
    assert record.name in response["text"]
    assert record.id not in response["text"]
