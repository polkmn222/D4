import sys
import types
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest
from sqlalchemy.orm import declarative_base
from unittest.mock import AsyncMock

if "db.database" not in sys.modules:
    fake_db_database = types.ModuleType("db.database")
    fake_db_database.Base = declarative_base()
    fake_db_database.engine = None
    fake_db_database.SessionLocal = None
    fake_db_database.get_db = lambda: None
    sys.modules["db.database"] = fake_db_database

from ai_agent.ui.backend.service import AiAgentService
from ai_agent.llm.backend.conversation_context import ConversationContextStore


@pytest.mark.asyncio
async def test_incomplete_create_lead_returns_chat_native_open_form():
    response = await AiAgentService.process_query(
        db=None,
        user_query="create lead",
        conversation_id="phase227-lead-form",
    )

    assert response["intent"] == "OPEN_FORM"
    assert response["object_type"] == "lead"
    assert response["form"]["mode"] == "create"
    assert response["form"]["required_fields"] == ["last_name", "status"]
    assert response["text"] == "I opened the lead create form here in chat. Fill in the fields you want, then save it."
    assert response["form"]["description"] == "Fill in the fields below, then save."
    assert any(field["name"] == "last_name" for field in response["form"]["fields"])


@pytest.mark.asyncio
async def test_incomplete_create_lead_includes_lookup_fields():
    response = await AiAgentService.process_query(
        db=None,
        user_query="create lead",
        conversation_id="phase233-lead-lookups",
    )

    fields = {field["name"]: field for field in response["form"]["fields"]}

    assert fields["product"]["control"] == "lookup"
    assert fields["product"]["lookup_object"] == "Product"
    assert fields["model"]["control"] == "lookup"
    assert fields["model"]["lookup_object"] == "Model"
    assert fields["brand"]["control"] == "lookup"
    assert fields["brand"]["lookup_object"] == "Brand"


@pytest.mark.asyncio
async def test_update_lead_without_fields_returns_schema_open_form_at_source():
    lead = SimpleNamespace(
        id="LEAD239",
        first_name="Ada",
        last_name="Kim",
        email="ada@example.com",
        phone="01012345678",
        status="New",
        gender="Female",
        product=None,
        model=None,
        brand=None,
        description="Priority lead",
    )

    with patch("web.backend.app.services.lead_service.LeadService.get_lead", return_value=lead):
        response = await AiAgentService.process_query(
            db=None,
            user_query="update lead LEAD239",
            conversation_id="phase239-update-lead",
        )

    assert response["intent"] == "OPEN_FORM"
    assert response["object_type"] == "lead"
    assert response.get("form")
    assert response["form"]["mode"] == "edit"
    assert response["text"] == "I opened the lead edit form for **Ada Kim** here in chat. Update the fields you want, then save your changes."
    assert response["form"]["description"] == "Update the fields below, then save your changes."


@pytest.mark.asyncio
async def test_partial_create_contact_prefills_chat_native_form():
    response = await AiAgentService.process_query(
        db=None,
        user_query="create contact first name Ada email ada@example.com",
        conversation_id="phase227-contact-form",
    )

    assert response["intent"] == "OPEN_FORM"
    assert response["form"]["required_fields"] == ["last_name"]
    field_values = {field["name"]: field.get("value") for field in response["form"]["fields"]}
    assert field_values["first_name"] == "Ada"
    assert field_values["email"] == "ada@example.com"
    assert field_values["last_name"] in ("", None)
    assert "status" not in field_values


@pytest.mark.asyncio
async def test_update_contact_without_fields_returns_schema_open_form_at_source():
    contact = SimpleNamespace(
        id="CONTACT239",
        first_name="Ada",
        last_name="Kim",
        email="ada@example.com",
        phone="01012345678",
        status="Qualified",
        gender="Female",
        website="https://example.com",
        tier="Gold",
        description="VIP contact",
    )

    with patch("web.backend.app.services.contact_service.ContactService.get_contact", return_value=contact):
        response = await AiAgentService.process_query(
            db=None,
            user_query="update contact CONTACT239",
            conversation_id="phase239-update-contact",
        )

    assert response["intent"] == "OPEN_FORM"
    assert response["object_type"] == "contact"
    assert response.get("form")
    assert response["form"]["mode"] == "edit"
    assert response["text"] == "I opened the contact edit form for **Ada Kim** here in chat. Update the fields you want, then save your changes."
    assert response["form"]["description"] == "Update the fields below, then save your changes."


@pytest.mark.asyncio
async def test_partial_create_contact_prefills_gender_website_and_tier():
    response = await AiAgentService.process_query(
        db=None,
        user_query="create contact first name Ada gender Female website https://example.com tier Gold",
        conversation_id="phase234-contact-scalars",
    )

    assert response["intent"] == "OPEN_FORM"
    field_values = {field["name"]: field.get("value") for field in response["form"]["fields"]}
    assert field_values["first_name"] == "Ada"
    assert field_values["gender"] == "Female"
    assert field_values["website"] == "https://example.com"
    assert field_values["tier"] == "Gold"


@pytest.mark.asyncio
async def test_edit_opportunity_returns_contact_brand_model_product_and_asset_lookup_fields():
    opportunity = SimpleNamespace(
        id="OPP227",
        name="Fleet Renewal",
        amount=120000,
        stage="Qualification",
        status="Open",
        probability=70,
        temperature="Warm",
        contact="CONTACT1",
        brand="BRAND1",
        model="MODEL1",
        product="PROD1",
        asset="ASSET1",
    )

    contact = SimpleNamespace(id="CONTACT1", first_name="Ada", last_name="Kim")
    brand = SimpleNamespace(id="BRAND1", name="Hyundai")
    model = SimpleNamespace(id="MODEL1", name="Sonata")
    product = SimpleNamespace(id="PROD1", name="Premium Plan")
    asset = SimpleNamespace(id="ASSET1", name="KMH123456789")

    with patch("web.backend.app.services.opportunity_service.OpportunityService.get_opportunity", return_value=opportunity), patch(
        "web.backend.app.services.contact_service.ContactService.get_contact",
        return_value=contact,
    ), patch(
        "ai_agent.ui.backend.service.VehicleSpecService.get_vehicle_spec",
        return_value=brand,
    ), patch(
        "ai_agent.ui.backend.service.ModelService.get_model",
        return_value=model,
    ), patch(
        "web.backend.app.services.product_service.ProductService.get_product",
        return_value=product,
    ), patch(
        "web.backend.app.services.asset_service.AssetService.get_asset",
        return_value=asset,
    ):
        response = await AiAgentService.process_query(
            db=None,
            user_query="edit opportunity OPP227",
            conversation_id="phase227-opp-edit",
        )

    assert response["intent"] == "OPEN_FORM"
    fields = {field["name"]: field for field in response["form"]["fields"]}
    assert set(fields) == {"contact", "brand", "model", "product", "asset", "name", "amount", "stage", "probability"}
    assert fields["contact"]["control"] == "lookup"
    assert fields["contact"]["lookup_object"] == "Contact"
    assert fields["contact"]["value"] == "CONTACT1"
    assert fields["contact"]["display_value"] == "Ada Kim"
    assert fields["brand"]["control"] == "lookup"
    assert fields["brand"]["lookup_object"] == "Brand"
    assert fields["brand"]["value"] == "BRAND1"
    assert fields["brand"]["display_value"] == "Hyundai"
    assert fields["model"]["control"] == "lookup"
    assert fields["model"]["lookup_object"] == "Model"
    assert fields["model"]["value"] == "MODEL1"
    assert fields["model"]["display_value"] == "Sonata"
    assert fields["product"]["control"] == "lookup"
    assert fields["product"]["lookup_object"] == "Product"
    assert fields["product"]["value"] == "PROD1"
    assert fields["product"]["display_value"] == "Premium Plan"
    assert fields["asset"]["control"] == "lookup"
    assert fields["asset"]["lookup_object"] == "Asset"
    assert fields["asset"]["value"] == "ASSET1"
    assert fields["asset"]["display_value"] == "KMH123456789"


@pytest.mark.asyncio
async def test_incomplete_create_opportunity_includes_contact_brand_model_product_and_asset_lookup_fields():
    response = await AiAgentService.process_query(
        db=None,
        user_query="create opportunity",
        conversation_id="phase235-opp-create",
    )

    assert response["intent"] == "OPEN_FORM"
    fields = {field["name"]: field for field in response["form"]["fields"]}
    assert fields["contact"]["control"] == "lookup"
    assert fields["contact"]["lookup_object"] == "Contact"
    assert fields["brand"]["control"] == "lookup"
    assert fields["brand"]["lookup_object"] == "Brand"
    assert fields["model"]["control"] == "lookup"
    assert fields["model"]["lookup_object"] == "Model"
    assert fields["product"]["control"] == "lookup"
    assert fields["product"]["lookup_object"] == "Product"
    assert fields["asset"]["control"] == "lookup"
    assert fields["asset"]["lookup_object"] == "Asset"
    assert "status" not in fields
    assert response["form"]["required_fields"] == ["contact", "name", "stage"]


@pytest.mark.asyncio
async def test_opportunity_edit_save_without_contact_field_can_reuse_existing_contact_requirement():
    opportunity = SimpleNamespace(
        id="OPP294",
        contact="CONTACT1",
        name="Fleet Renewal",
        amount=120000,
        stage="Qualification",
        status="Open",
        probability=70,
    )

    fake_db = object()
    with patch("web.backend.app.services.opportunity_service.OpportunityService.get_opportunity", return_value=opportunity), patch(
        "web.backend.app.services.opportunity_service.OpportunityService.update_opportunity",
        return_value=opportunity,
    ):
        response = await AiAgentService.submit_chat_native_form(
            db=fake_db,
            object_type="opportunity",
            mode="edit",
            record_id="OPP294",
            values={
                "name": "Fleet Renewal",
                "stage": "Qualification",
                "amount": "120000",
                "probability": "70",
            },
            conversation_id="phase295-opportunity-edit-save",
            language_preference="eng",
        )

    assert response["intent"] == "OPEN_RECORD"


@pytest.mark.asyncio
async def test_ai_recommend_bypasses_llm_and_returns_recommend_results():
    mocked_execute = AsyncMock(return_value={"intent": "RECOMMEND", "object_type": "opportunity", "results": []})
    mocked_llm = AsyncMock()
    with patch.object(AiAgentService, "_execute_intent", mocked_execute), patch.object(AiAgentService, "_call_multi_llm_ensemble", mocked_llm):
        response = await AiAgentService.process_query(
            db=None,
            user_query="AI Recommend",
            conversation_id="phase294-ai-recommend",
        )

    assert response["intent"] == "RECOMMEND"
    mocked_llm.assert_not_awaited()
    mocked_execute.assert_awaited()


@pytest.mark.asyncio
async def test_change_ai_recommend_bypasses_llm_and_routes_to_modify_ui():
    mocked_execute = AsyncMock(return_value={"intent": "CHAT", "text": "mode options"})
    mocked_llm = AsyncMock()
    with patch.object(AiAgentService, "_execute_intent", mocked_execute), patch.object(AiAgentService, "_call_multi_llm_ensemble", mocked_llm):
        response = await AiAgentService.process_query(
            db=None,
            user_query="Change AI Recommend",
            conversation_id="phase294-change-recommend",
        )

    assert response["intent"] == "CHAT"
    mocked_llm.assert_not_awaited()
    execute_payload = mocked_execute.await_args.args[1]
    assert execute_payload["intent"] == "MODIFY_UI"


@pytest.mark.asyncio
async def test_recommend_mode_follow_up_after_change_prompt_stays_in_recommendation_flow():
    ConversationContextStore.clear("phase300-change-followup")
    mocked_llm = AsyncMock()
    with patch.object(AiAgentService, "_call_multi_llm_ensemble", mocked_llm), patch(
        "ai_agent.llm.backend.recommendations.AIRecommendationService.get_recommendation_mode",
        return_value="Closing Soon",
    ):
        first = await AiAgentService.process_query(
            db=None,
            user_query="Change AI Recommend",
            conversation_id="phase300-change-followup",
        )
        second = await AiAgentService.process_query(
            db=None,
            user_query="Hot Deals",
            conversation_id="phase300-change-followup",
        )

    assert first["intent"] == "CHAT"
    assert "How would you like to change it?" in first["text"]
    assert second["intent"] == "MODIFY_UI"
    assert "Hot Deals" in second["text"]
    mocked_llm.assert_not_awaited()


@pytest.mark.asyncio
async def test_send_message_without_selection_opens_guided_messaging_workspace():
    mocked_llm = AsyncMock()
    with patch.object(AiAgentService, "_call_multi_llm_ensemble", mocked_llm):
        response = await AiAgentService.process_query(
            db=None,
            user_query="Send Message",
            conversation_id="phase300-send-guided",
        )

    assert response["intent"] == "SEND_MESSAGE"
    assert response["redirect_url"] == "/messaging/ui"
    assert "Start by picking recipients" in response["text"]
    mocked_llm.assert_not_awaited()


@pytest.mark.asyncio
async def test_recommend_uses_dashboard_sendable_limit_and_source():
    recommend_rows = [
        SimpleNamespace(id="OPP1", name="A", amount=1, stage="Test Drive", temp_display="Hot", created_at=None),
        SimpleNamespace(id="OPP2", name="B", amount=2, stage="Test Drive", temp_display="Hot", created_at=None),
    ]

    with patch(
        "ai_agent.llm.backend.recommendations.AIRecommendationService.get_sendable_recommendations",
        return_value=recommend_rows,
    ) as mocked_sendable, patch(
        "ai_agent.llm.backend.recommendations.AIRecommendationService.get_recommendation_mode",
        return_value="Hot Deals",
    ):
        response = await AiAgentService._execute_intent(
            db=None,
            agent_output={"intent": "RECOMMEND", "object_type": "opportunity"},
            user_query="AI Recommend",
            conversation_id="phase296-recommend",
        )

    mocked_sendable.assert_called_once()
    assert mocked_sendable.call_args.kwargs == {}
    assert response["intent"] == "RECOMMEND"
    assert len(response["results"]) == 2


@pytest.mark.asyncio
async def test_recently_created_opportunities_routes_to_query_before_create():
    mocked_execute = AsyncMock(return_value={"intent": "QUERY", "object_type": "opportunity", "results": []})
    with patch.object(AiAgentService, "_execute_intent", mocked_execute):
        response = await AiAgentService.process_query(
            db=None,
            user_query="최근에 생성 된 기회들",
            conversation_id="phase294-recent-opps",
        )

    assert response["intent"] == "QUERY"
    execute_payload = mocked_execute.await_args.args[1]
    assert execute_payload["intent"] == "QUERY"
    assert execute_payload["object_type"] == "opportunity"


@pytest.mark.asyncio
async def test_update_opportunity_without_fields_returns_schema_open_form_at_source():
    opportunity = SimpleNamespace(
        id="OPP239",
        contact="CONTACT1",
        brand="BRAND1",
        model="MODEL1",
        product="PROD1",
        asset="ASSET1",
        name="Fleet Renewal",
        amount=120000,
        stage="Qualification",
        status="Open",
        probability=70,
        temperature="Warm",
    )

    with patch("web.backend.app.services.opportunity_service.OpportunityService.get_opportunity", return_value=opportunity), patch(
        "web.backend.app.services.contact_service.ContactService.get_contact",
        return_value=SimpleNamespace(id="CONTACT1", first_name="Ada", last_name="Kim"),
    ), patch(
        "ai_agent.ui.backend.service.VehicleSpecService.get_vehicle_spec",
        return_value=SimpleNamespace(id="BRAND1", name="Hyundai"),
    ), patch(
        "ai_agent.ui.backend.service.ModelService.get_model",
        return_value=SimpleNamespace(id="MODEL1", name="Sonata"),
    ), patch(
        "web.backend.app.services.product_service.ProductService.get_product",
        return_value=SimpleNamespace(id="PROD1", name="Premium Plan"),
    ), patch(
        "web.backend.app.services.asset_service.AssetService.get_asset",
        return_value=SimpleNamespace(id="ASSET1", name="KMH123456789"),
    ):
        response = await AiAgentService.process_query(
            db=None,
            user_query="update opportunity OPP239",
            conversation_id="phase239-update-opportunity",
        )

    assert response["intent"] == "OPEN_FORM"
    assert response["object_type"] == "opportunity"
    assert response.get("form")
    assert response["form"]["mode"] == "edit"
    assert response["text"] == "I opened the opportunity edit form for **Fleet Renewal** here in chat. Update the fields you want, then save your changes."
    assert response["form"]["description"] == "Update the fields below, then save your changes."


@pytest.mark.asyncio
async def test_submit_chat_native_lead_create_returns_open_record():
    lead = SimpleNamespace(
        id="LEAD227",
        first_name="Ada",
        last_name="Kim",
        email="ada@example.com",
        phone="01012345678",
        status="New",
        gender="Female",
        brand=None,
        model=None,
        product=None,
        description="Priority lead",
    )

    with patch("web.backend.app.services.lead_service.LeadService.create_lead", return_value=lead):
        response = await AiAgentService.submit_chat_native_form(
            db=None,
            object_type="lead",
            mode="create",
            values={
                "first_name": "Ada",
                "last_name": "Kim",
                "email": "ada@example.com",
                "phone": "01012345678",
                "status": "New",
                "gender": "Female",
                "description": "Priority lead",
            },
            conversation_id="phase227-submit-create",
            language_preference="eng",
        )

    assert response["intent"] == "OPEN_RECORD"
    assert response["object_type"] == "lead"
    assert response["record_id"] == "LEAD227"
    assert "has been created. The record is open below." in response["text"]
    card = response["chat_card"]
    assert card["type"] == "lead_paste"
    assert card["subtitle"] == "Lead · New"
    assert [action["action"] for action in card["actions"]] == ["open", "edit", "delete", "send_message"]
    assert "edit this lead" in card["hint"]
    assert "open the full record" in card["hint"]


@pytest.mark.asyncio
async def test_edit_lead_chat_native_form_preloads_lookup_display_values():
    lead = SimpleNamespace(
        id="LEAD233",
        first_name="Ada",
        last_name="Kim",
        email="ada@example.com",
        phone="01012345678",
        status="New",
        gender="Female",
        product="01t000000000001AAA",
        model="a0M000000000001AAA",
        brand="a0B000000000001AAA",
        description="Priority lead",
    )

    with patch("web.backend.app.services.lead_service.LeadService.get_lead", return_value=lead), patch(
        "web.backend.app.services.product_service.ProductService.get_product",
        return_value=SimpleNamespace(id="01t000000000001AAA", name="Premium Plan"),
    ), patch(
        "ai_agent.ui.backend.service.ModelService.get_model",
        return_value=SimpleNamespace(id="a0M000000000001AAA", name="Sonata"),
    ), patch(
        "ai_agent.ui.backend.service.VehicleSpecService.get_vehicle_spec",
        return_value=SimpleNamespace(id="a0B000000000001AAA", name="Hyundai"),
    ):
        response = await AiAgentService.process_query(
            db=None,
            user_query="edit lead LEAD233",
            conversation_id="phase233-lead-edit",
        )

    fields = {field["name"]: field for field in response["form"]["fields"]}
    assert fields["product"]["value"] == "01t000000000001AAA"
    assert fields["product"]["display_value"] == "Premium Plan"
    assert fields["model"]["value"] == "a0M000000000001AAA"
    assert fields["model"]["display_value"] == "Sonata"
    assert fields["brand"]["value"] == "a0B000000000001AAA"
    assert fields["brand"]["display_value"] == "Hyundai"


@pytest.mark.asyncio
async def test_submit_chat_native_lead_create_passes_lookup_ids():
    lead = SimpleNamespace(
        id="LEAD233C",
        first_name="Ada",
        last_name="Kim",
        email="ada@example.com",
        phone="01012345678",
        status="New",
        gender="Female",
        product="01t000000000001AAA",
        model="a0M000000000001AAA",
        brand="a0B000000000001AAA",
        description="Priority lead",
    )

    with patch("web.backend.app.services.lead_service.LeadService.create_lead", return_value=lead) as create_lead, patch(
        "ai_agent.ui.backend.service.VehicleSpecService.get_vehicle_spec",
        return_value=SimpleNamespace(id="a0B000000000001AAA", name="Hyundai"),
    ), patch(
        "ai_agent.ui.backend.service.ModelService.get_model",
        return_value=SimpleNamespace(id="a0M000000000001AAA", name="Sonata"),
    ), patch(
        "web.backend.app.services.product_service.ProductService.get_product",
        return_value=SimpleNamespace(id="01t000000000001AAA", name="Premium Plan"),
    ):
        response = await AiAgentService.submit_chat_native_form(
            db=None,
            object_type="lead",
            mode="create",
            values={
                "first_name": "Ada",
                "last_name": "Kim",
                "email": "ada@example.com",
                "phone": "01012345678",
                "status": "New",
                "gender": "Female",
                "product": "01t000000000001AAA",
                "model": "a0M000000000001AAA",
                "brand": "a0B000000000001AAA",
                "description": "Priority lead",
            },
            conversation_id="phase233-submit-create",
            language_preference="eng",
        )

    assert response["intent"] == "OPEN_RECORD"
    kwargs = create_lead.call_args.kwargs
    assert kwargs["product"] == "01t000000000001AAA"
    assert kwargs["model"] == "a0M000000000001AAA"
    assert kwargs["brand"] == "a0B000000000001AAA"


@pytest.mark.asyncio
async def test_submit_chat_native_opportunity_edit_validation_error_returns_open_form():
    opportunity = SimpleNamespace(
        id="OPP227E",
        name="Fleet Renewal",
        amount=120000,
        stage="Qualification",
        status="Open",
        probability=70,
        temperature="Warm",
    )

    with patch("web.backend.app.services.opportunity_service.OpportunityService.get_opportunity", return_value=opportunity):
        response = await AiAgentService.submit_chat_native_form(
            db=None,
            object_type="opportunity",
            mode="edit",
            record_id="OPP227E",
            values={
                "name": "Fleet Renewal",
                "amount": "120000",
                "stage": "Qualification",
                "status": "Open",
                "probability": "120",
                "temperature": "Warm",
            },
            conversation_id="phase227-submit-edit",
            language_preference="eng",
        )

    assert response["intent"] == "OPEN_FORM"
    assert response["form"]["field_errors"]["probability"] == "Probability must be between 0 and 100."


@pytest.mark.asyncio
async def test_submit_chat_native_opportunity_create_passes_contact_id():
    opportunity = SimpleNamespace(
        id="OPP235",
        contact="CONTACT1",
        brand="BRAND1",
        model="MODEL1",
        product="PROD1",
        asset="ASSET1",
        name="Fleet Renewal",
        amount=120000,
        stage="Qualification",
        status="Open",
        probability=70,
        temperature="Warm",
    )

    with patch("web.backend.app.services.opportunity_service.OpportunityService.create_opportunity", return_value=opportunity) as create_opportunity:
        response = await AiAgentService.submit_chat_native_form(
            db=None,
            object_type="opportunity",
            mode="create",
            values={
                "contact": "CONTACT1",
                "brand": "BRAND1",
                "model": "MODEL1",
                "product": "PROD1",
                "asset": "ASSET1",
                "name": "Fleet Renewal",
                "amount": "120000",
                "stage": "Qualification",
                "status": "Open",
                "probability": "70",
                "temperature": "Warm",
            },
            conversation_id="phase235-opp-submit",
            language_preference="eng",
        )

    assert response["intent"] == "OPEN_RECORD"
    kwargs = create_opportunity.call_args.kwargs
    assert kwargs["contact"] == "CONTACT1"
    assert kwargs["brand"] == "BRAND1"
    assert kwargs["model"] == "MODEL1"
    assert kwargs["product"] == "PROD1"
    assert kwargs["asset"] == "ASSET1"


@pytest.mark.asyncio
async def test_contact_open_record_response_uses_consistent_record_card_shape():
    contact = SimpleNamespace(
        id="CONTACT241",
        first_name="Ada",
        last_name="Kim",
        email="ada@example.com",
        phone="01012345678",
        status="Qualified",
    )

    with patch("web.backend.app.services.contact_service.ContactService.update_contact", return_value=contact):
        response = await AiAgentService.submit_chat_native_form(
            db=None,
            object_type="contact",
            mode="edit",
            record_id="CONTACT241",
            values={"last_name": "Kim", "status": "Qualified"},
            conversation_id="phase241-contact-shape",
            language_preference="eng",
        )

    card = response["chat_card"]
    assert response["intent"] == "OPEN_RECORD"
    assert "has been updated. The refreshed record is open below." in response["text"]
    assert card["type"] == "record_paste"
    assert card["subtitle"] == "Contact · Qualified"
    assert [field["label"] for field in card["fields"]] == ["First name", "Last name", "Status", "Email", "Phone"]
    assert [action["action"] for action in card["actions"]] == ["open", "edit", "delete", "send_message"]
    assert "edit this contact" in card["hint"]
    assert "send a message" in card["hint"]


@pytest.mark.asyncio
async def test_opportunity_open_record_response_uses_consistent_record_card_shape():
    opportunity = SimpleNamespace(
        id="OPP241",
        contact="CONTACT241",
        name="Fleet Renewal",
        stage="Qualification",
        status="Open",
        amount=120000,
        probability=70,
    )

    with patch("web.backend.app.services.opportunity_service.OpportunityService.update_opportunity", return_value=opportunity):
        response = await AiAgentService.submit_chat_native_form(
            db=None,
            object_type="opportunity",
            mode="edit",
            record_id="OPP241",
            values={"contact": "CONTACT241", "name": "Fleet Renewal", "stage": "Qualification", "amount": "120000"},
            conversation_id="phase241-opp-shape",
            language_preference="eng",
        )

    card = response["chat_card"]
    assert response["intent"] == "OPEN_RECORD"
    assert "has been updated. The refreshed record is open below." in response["text"]
    assert card["type"] == "record_paste"
    assert card["subtitle"] == "Opportunity · Qualification"
    assert [field["label"] for field in card["fields"]] == ["Contact", "Name", "Amount", "Stage", "Brand", "Model", "Product", "Asset", "Probability"]
    assert [action["action"] for action in card["actions"]] == ["open", "edit", "delete", "send_message"]
    assert "edit this opportunity" in card["hint"]
    assert "send a message" in card["hint"]


@pytest.mark.asyncio
async def test_submit_ai_managed_brand_edit_returns_open_record():
    brand = SimpleNamespace(id="BRAND332", name="Northstar", record_type="Brand", description="Flagship brand")

    with patch("ai_agent.ui.backend.service.VehicleSpecService.update_vehicle_spec", return_value=brand):
        response = await AiAgentService.submit_chat_native_form(
            db=None,
            object_type="brand",
            mode="edit",
            record_id="BRAND332",
            values={"name": "Northstar", "description": "Flagship brand"},
            conversation_id="phase332-brand-edit",
            language_preference="eng",
        )

    assert response["intent"] == "OPEN_RECORD"
    assert response["object_type"] == "brand"
    assert response["record_id"] == "BRAND332"
    assert response["redirect_url"] == "/vehicle_specifications/BRAND332"


@pytest.mark.asyncio
async def test_submit_ai_managed_model_edit_normalizes_brand_lookup_and_returns_open_record():
    model = SimpleNamespace(id="MODEL332", name="Voyage 9", brand="BRAND332", description="Touring trim")

    with patch("ai_agent.ui.backend.service.ModelService.get_model", return_value=model), patch(
        "ai_agent.ui.backend.service.AiAgentService._resolve_lookup_name_to_id", return_value="BRAND332"
    ), patch(
        "ai_agent.ui.backend.service.VehicleSpecService.get_vehicle_spec", return_value=SimpleNamespace(id="BRAND332", name="Northstar")
    ), patch(
        "ai_agent.ui.backend.service.VehicleSpecService.get_vehicle_specs", return_value=[SimpleNamespace(id="BRAND332", name="Northstar")]
    ), patch(
        "ai_agent.ui.backend.service.ModelService.update_model", return_value=model
    ) as update_model:
        response = await AiAgentService.submit_chat_native_form(
            db=object(),
            object_type="model",
            mode="edit",
            record_id="MODEL332",
            values={"name": "Voyage 9", "brand": "Northstar", "description": "Touring trim"},
            conversation_id="phase332-model-edit",
            language_preference="eng",
        )

    assert response["intent"] == "OPEN_RECORD"
    assert response["object_type"] == "model"
    assert update_model.call_args.kwargs["brand"] == "BRAND332"


@pytest.mark.asyncio
async def test_submit_ai_managed_asset_edit_returns_open_record():
    asset = SimpleNamespace(id="ASSET332", name="Aureline Atlas 11", vin="VIN332", status="Active", brand="BRAND1", model="MODEL1")

    with patch("web.backend.app.services.asset_service.AssetService.update_asset", return_value=asset), patch(
        "ai_agent.ui.backend.service.VehicleSpecService.get_vehicle_spec", return_value=SimpleNamespace(id="BRAND1", name="Aureline")
    ), patch(
        "ai_agent.ui.backend.service.ModelService.get_model", return_value=SimpleNamespace(id="MODEL1", name="Atlas 11")
    ):
        response = await AiAgentService.submit_chat_native_form(
            db=None,
            object_type="asset",
            mode="edit",
            record_id="ASSET332",
            values={"name": "Aureline Atlas 11", "vin": "VIN332", "status": "Active"},
            conversation_id="phase332-asset-edit",
            language_preference="eng",
        )

    assert response["intent"] == "OPEN_RECORD"
    assert response["object_type"] == "asset"
    assert response["record_id"] == "ASSET332"
    assert response["redirect_url"] == "/assets/ASSET332"


@pytest.mark.asyncio
async def test_submit_ai_managed_message_template_edit_returns_open_record():
    template = SimpleNamespace(
        id="TPL332",
        name="Owner Outreach 12",
        record_type="LMS",
        subject="Updated subject",
        content="Updated content",
        image_url="",
    )

    with patch("web.message.backend.services.message_template_service.MessageTemplateService.update_template", return_value=template):
        response = await AiAgentService.submit_chat_native_form(
            db=None,
            object_type="message_template",
            mode="edit",
            record_id="TPL332",
            values={"name": "Owner Outreach 12", "record_type": "LMS", "subject": "Updated subject", "content": "Updated content"},
            conversation_id="phase332-template-edit",
            language_preference="eng",
        )

    assert response["intent"] == "OPEN_RECORD"
    assert response["object_type"] == "message_template"
    assert response["record_id"] == "TPL332"
    assert response["redirect_url"] == "/message_templates/TPL332"


@pytest.mark.asyncio
async def test_manage_product_returns_open_record_with_product_chat_card():
    product = SimpleNamespace(
        id="PROD241",
        name="Premium Plan",
        category="Warranty",
        brand="BRAND1",
        model="MODEL1",
        base_price=120000,
    )
    brand = SimpleNamespace(id="BRAND1", name="Hyundai")
    model = SimpleNamespace(id="MODEL1", name="Sonata")

    with patch("web.backend.app.services.product_service.ProductService.get_product", return_value=product), patch(
        "web.backend.app.services.vehicle_spec_service.VehicleSpecService.get_vehicle_spec", return_value=brand
    ), patch(
        "ai_agent.ui.backend.service.ModelService.get_model", return_value=model
    ):
        response = await AiAgentService.process_query(
            db=None,
            user_query="Manage product PROD241",
            conversation_id="phase256-product-manage",
            language_preference="eng",
        )

    card = response["chat_card"]
    assert response["intent"] == "OPEN_RECORD"
    assert response["object_type"] == "product"
    assert response["record_id"] == "PROD241"
    assert response["redirect_url"] == "/products/PROD241"
    assert "Product **Premium Plan** is now open." in response["text"]
    assert card["type"] == "record_paste"
    assert card["subtitle"] == "Product · Warranty"
    assert [field["label"] for field in card["fields"]] == ["Name", "Category", "Brand", "Model", "Base Price"]
    assert [action["action"] for action in card["actions"]] == ["open", "edit", "delete"]
    assert "edit this product" in card["hint"]


@pytest.mark.asyncio
async def test_manage_asset_returns_open_record_with_asset_chat_card():
    asset = SimpleNamespace(
        id="ASSET257",
        name="Executive Demo",
        vin="KMH123456789",
        status="Active",
        product="PROD1",
        brand="BRAND1",
        model="MODEL1",
    )
    product = SimpleNamespace(id="PROD1", name="Premium Plan")
    brand = SimpleNamespace(id="BRAND1", name="Hyundai")
    model = SimpleNamespace(id="MODEL1", name="Sonata")

    with patch("web.backend.app.services.asset_service.AssetService.get_asset", return_value=asset), patch(
        "web.backend.app.services.product_service.ProductService.get_product", return_value=product
    ), patch(
        "web.backend.app.services.vehicle_spec_service.VehicleSpecService.get_vehicle_spec", return_value=brand
    ), patch(
        "ai_agent.ui.backend.service.ModelService.get_model", return_value=model
    ):
        response = await AiAgentService.process_query(
            db=None,
            user_query="Manage asset ASSET257",
            conversation_id="phase257-asset-manage",
            language_preference="eng",
        )

    card = response["chat_card"]
    assert response["intent"] == "OPEN_RECORD"
    assert response["object_type"] == "asset"
    assert response["record_id"] == "ASSET257"
    assert response["redirect_url"] == "/assets/ASSET257"
    assert "Asset **Executive Demo** is now open." in response["text"]
    assert card["type"] == "record_paste"
    assert card["subtitle"] == "Asset · Active"
    assert [field["label"] for field in card["fields"]] == ["Name", "VIN", "Status", "Product", "Brand", "Model"]
    assert [action["action"] for action in card["actions"]] == ["open", "edit", "delete"]
    assert "edit this asset" in card["hint"]


@pytest.mark.asyncio
async def test_manage_brand_returns_open_record_with_brand_chat_card():
    brand = SimpleNamespace(
        id="BRAND258",
        name="Hyundai",
        record_type="Brand",
        description="Passenger vehicle lineup",
    )

    with patch("web.backend.app.services.vehicle_spec_service.VehicleSpecService.get_vehicle_spec", return_value=brand):
        response = await AiAgentService.process_query(
            db=None,
            user_query="Manage brand BRAND258",
            conversation_id="phase258-brand-manage",
            language_preference="eng",
        )

    card = response["chat_card"]
    assert response["intent"] == "OPEN_RECORD"
    assert response["object_type"] == "brand"
    assert response["record_id"] == "BRAND258"
    assert response["redirect_url"] == "/vehicle_specifications/BRAND258"
    assert "Brand **Hyundai** is now open." in response["text"]
    assert card["type"] == "record_paste"
    assert card["subtitle"] == "Brand · Brand"
    assert [field["label"] for field in card["fields"]] == ["Name", "Type", "Description"]
    assert [action["action"] for action in card["actions"]] == ["open", "edit", "delete"]
    assert "edit this brand" in card["hint"]


@pytest.mark.asyncio
async def test_manage_model_returns_open_record_with_model_chat_card():
    model = SimpleNamespace(
        id="MODEL259",
        name="Sonata",
        brand="BRAND1",
        description="Mid-size sedan",
    )
    brand = SimpleNamespace(id="BRAND1", name="Hyundai")

    with patch("ai_agent.ui.backend.service.ModelService.get_model", return_value=model), patch(
        "web.backend.app.services.vehicle_spec_service.VehicleSpecService.get_vehicle_spec", return_value=brand
    ):
        response = await AiAgentService.process_query(
            db=None,
            user_query="Manage model MODEL259",
            conversation_id="phase259-model-manage",
            language_preference="eng",
        )

    card = response["chat_card"]
    assert response["intent"] == "OPEN_RECORD"
    assert response["object_type"] == "model"
    assert response["record_id"] == "MODEL259"
    assert response["redirect_url"] == "/models/MODEL259"
    assert "Model **Sonata** is now open." in response["text"]
    assert card["type"] == "record_paste"
    assert card["subtitle"] == "Model · Hyundai"
    assert [field["label"] for field in card["fields"]] == ["Name", "Brand", "Description"]
    assert [action["action"] for action in card["actions"]] == ["open", "edit", "delete"]
    assert "edit this model" in card["hint"]


@pytest.mark.asyncio
async def test_manage_message_template_returns_open_record_with_template_chat_card():
    template = SimpleNamespace(
        id="TEMPLATE260",
        name="Spring Promo",
        record_type="MMS",
        subject="Seasonal Offer",
        content="Upgrade today.",
        image_url="/static/uploads/templates/spring.jpg",
        file_path=None,
    )

    with patch("web.message.backend.services.message_template_service.MessageTemplateService.get_template", return_value=template):
        response = await AiAgentService.process_query(
            db=None,
            user_query="Manage message_template TEMPLATE260",
            conversation_id="phase260-template-manage",
            language_preference="eng",
        )

    card = response["chat_card"]
    assert response["intent"] == "OPEN_RECORD"
    assert response["object_type"] == "message_template"
    assert response["record_id"] == "TEMPLATE260"
    assert response["redirect_url"] == "/message_templates/TEMPLATE260"
    assert "Message Template **Spring Promo** is now open." in response["text"]
    assert card["type"] == "record_paste"
    assert card["subtitle"] == "Template · MMS"
    assert [field["label"] for field in card["fields"]] == ["Name", "Type", "Subject", "Content", "Image"]
    assert [action["action"] for action in card["actions"]] == ["open", "edit", "delete", "preview_image", "use_in_send"]
    assert card["actions"][3]["url"] == "/static/uploads/templates/spring.jpg"
    assert "Send Message" in card["hint"]


@pytest.mark.asyncio
async def test_show_messages_resolves_to_message_send_query_list_behavior():
    paged = {
        "results": [
            {"id": "MSG1", "contact": "Ada Kim", "direction": "Outbound", "status": "Sent", "sent_at": "2026-03-27T10:00:00"},
            {"id": "MSG2", "contact": "Min Park", "direction": "Outbound", "status": "Sent", "sent_at": "2026-03-27T09:00:00"},
        ],
        "sql": "SELECT ms.id, TRIM(CONCAT_WS(' ', c.first_name, c.last_name)) AS contact, ms.direction, ms.status, ms.sent_at FROM message_sends ms LEFT JOIN contacts c ON ms.contact = c.id WHERE ms.deleted_at IS NULL ORDER BY ms.sent_at DESC",
        "pagination": {"page": 1, "per_page": 30, "total": 2, "total_pages": 1, "object_type": "message_send"},
    }

    with patch.object(AiAgentService, "_execute_paginated_query", return_value=paged) as execute_paginated:
        response = await AiAgentService.process_query(
            db=None,
            user_query="show messages",
            conversation_id="phase262-show-messages",
            language_preference="eng",
        )

    assert response["intent"] == "QUERY"
    assert response["object_type"] == "message_send"
    assert response["results"] == paged["results"]
    assert response["pagination"]["total"] == 2
    assert response["text"] == "I found 2 messages for you."
    execute_paginated.assert_called_once()
    assert "FROM message_sends ms" in execute_paginated.call_args.args[1]
    assert "ORDER BY ms.sent_at DESC" in execute_paginated.call_args.args[1]


@pytest.mark.asyncio
async def test_show_recent_messages_returns_message_send_list_ordered_by_sent_at_desc():
    paged = {
        "results": [
            {"id": "MSG3", "contact": "Ada Kim", "direction": "Outbound", "status": "Sent", "sent_at": "2026-03-27T11:00:00"},
        ],
        "sql": "SELECT ms.id, TRIM(CONCAT_WS(' ', c.first_name, c.last_name)) AS contact, ms.direction, ms.status, ms.sent_at FROM message_sends ms LEFT JOIN contacts c ON ms.contact = c.id WHERE ms.deleted_at IS NULL ORDER BY ms.sent_at DESC",
        "pagination": {"page": 1, "per_page": 30, "total": 1, "total_pages": 1, "object_type": "message_send"},
    }

    with patch.object(AiAgentService, "_execute_paginated_query", return_value=paged) as execute_paginated:
        response = await AiAgentService.process_query(
            db=None,
            user_query="show recent messages",
            conversation_id="phase262-recent-messages",
            language_preference="eng",
        )

    assert response["intent"] == "QUERY"
    assert response["object_type"] == "message_send"
    assert response["results"] == paged["results"]
    assert response["text"] == "I found 1 message for you."
    execute_paginated.assert_called_once()
    assert "ORDER BY ms.sent_at DESC" in execute_paginated.call_args.args[1]


@pytest.mark.asyncio
async def test_edit_contact_chat_native_form_preloads_gender_and_scalar_fields():
    contact = SimpleNamespace(
        id="CONTACT234",
        first_name="Ada",
        last_name="Kim",
        email="ada@example.com",
        phone="01012345678",
        status="Qualified",
        gender="Female",
        website="https://example.com",
        tier="Gold",
        description="VIP contact",
    )

    with patch("web.backend.app.services.contact_service.ContactService.get_contact", return_value=contact):
        response = await AiAgentService.process_query(
            db=None,
            user_query="edit contact CONTACT234",
            conversation_id="phase234-contact-edit",
        )

    fields = {field["name"]: field for field in response["form"]["fields"]}
    assert fields["gender"]["control"] == "select"
    assert fields["gender"]["value"] == "Female"
    assert fields["website"]["value"] == "https://example.com"
    assert fields["tier"]["value"] == "Gold"
    assert "status" not in fields


@pytest.mark.asyncio
async def test_submit_chat_native_contact_edit_uses_updated_record_without_extra_refetch():
    contact = SimpleNamespace(
        id="CONTACT232",
        first_name="Ada",
        last_name="Kim",
        email="ada@example.com",
        phone="01012345678",
        status="Qualified",
        gender="Female",
        website="https://example.com",
        tier="Gold",
        description="VIP contact",
    )

    with patch("web.backend.app.services.contact_service.ContactService.update_contact", return_value=contact) as update_contact, patch(
        "web.backend.app.services.contact_service.ContactService.get_contact"
    ) as get_contact:
        response = await AiAgentService.submit_chat_native_form(
            db=None,
            object_type="contact",
            mode="edit",
            record_id="CONTACT232",
            values={
                "first_name": "Ada",
                "last_name": "Kim",
                "email": "ada@example.com",
                "phone": "01012345678",
                "gender": "Female",
                "website": "https://example.com",
                "tier": "Gold",
            },
            conversation_id="phase232-contact-update",
            language_preference="eng",
        )

    assert response["intent"] == "OPEN_RECORD"
    assert response["record_id"] == "CONTACT232"
    update_contact.assert_called_once()
    get_contact.assert_not_called()
    kwargs = update_contact.call_args.kwargs
    assert kwargs["gender"] == "Female"
    assert kwargs["website"] == "https://example.com"
    assert kwargs["tier"] == "Gold"


def test_ai_agent_frontend_has_schema_open_form_branch_and_submit_endpoint():
    source = Path("development/ai_agent/ui/frontend/static/js/ai_agent.js").read_text(encoding="utf-8")

    assert "if (data.intent === 'OPEN_FORM' && data.form?.fields) {" in source
    assert "appendAgentSchemaFormMessage(data.text || 'I opened the form for you.', data.form);" in source
    assert "appendAgentInlineFormMessage(data.text || 'I opened the form for you.', data.form_url, data.form_title || 'Form');" in source
    assert "fetchAiAgentWithTimeout(form.action || formUrl" in source or "fetchAiAgentWithTimeout('/ai-agent/api/form-submit'" in source
    assert "function renderAgentInlineSchemaForm(form) {" in source
    assert "function submitAgentChatForm(event) {" in source


def test_ai_agent_frontend_uses_chat_native_form_card_not_workspace_for_schema_forms():
    source = Path("development/ai_agent/ui/frontend/static/js/ai_agent.js").read_text(encoding="utf-8")
    branch_start = source.index("if (data.intent === 'OPEN_FORM' && data.form?.fields) {")
    branch_end = source.index("if (data.text) {", branch_start)
    branch = source[branch_start:branch_end]

    assert "openAgentWorkspace" not in branch
    assert "appendAgentSchemaFormMessage" in branch


def test_ai_agent_frontend_prefers_web_inline_form_when_form_url_exists():
    source = Path("development/ai_agent/ui/frontend/static/js/ai_agent.js").read_text(encoding="utf-8")
    send_start = source.index("async function sendAiMessage(")
    send_end = source.index("function consumePendingDeleteShortcut(")
    send_source = source[send_start:send_end]
    url_branch = send_source.index("if (data.intent === 'OPEN_FORM' && data.form_url) {")
    schema_branch = send_source.index("if (data.intent === 'OPEN_FORM' && data.form?.fields) {")

    assert url_branch < schema_branch


def test_message_template_chat_card_contract_includes_edit_and_delete_actions():
    source = Path("development/ai_agent/ui/backend/service.py").read_text(encoding="utf-8")
    start = source.index("def _build_message_template_chat_card")
    end = source.index("def _build_phase1_open_record_response", start)
    branch = source[start:end]
    assert '{"label": "Edit", "action": "edit", "tone": "secondary"}' in branch
    assert '{"label": "Delete", "action": "delete", "tone": "danger"}' in branch


def test_ai_agent_frontend_scrolls_chat_native_form_into_view_on_initial_render():
    source = Path("development/ai_agent/ui/frontend/static/js/ai_agent.js").read_text(encoding="utf-8")

    assert "function scrollAgentSchemaFormIntoView(target) {" in source
    assert "scrollAgentSchemaFormIntoView(msgDiv);" in source
    assert "target.scrollIntoView({ behavior: 'smooth', block: 'start' });" in source


def test_ai_agent_frontend_uses_field_layout_metadata_for_inline_schema_form_grid():
    source = Path("development/ai_agent/ui/frontend/static/js/ai_agent.js").read_text(encoding="utf-8")

    assert "const layoutClass = field.layout === 'full' ? 'agent-chat-form-field-full' : '';" in source
    assert '<label class="agent-chat-form-field ${layoutClass}">' in source


def test_ai_agent_frontend_scrolls_replaced_form_after_validation_refresh():
    source = Path("development/ai_agent/ui/frontend/static/js/ai_agent.js").read_text(encoding="utf-8")

    assert "const replacementCard = wrapper.firstElementChild;" in source
    assert "card.replaceWith(replacementCard);" in source
    assert "scrollAgentSchemaFormIntoView(replacementCard);" in source


def test_ai_agent_frontend_routes_phase_objects_selection_edit_through_chat_forms():
    source = Path("development/ai_agent/ui/frontend/static/js/ai_agent.js").read_text(encoding="utf-8")
    edit_start = source.index("function triggerSelectionEdit() {")
    edit_end = source.index("function triggerSelectionDelete()", edit_start)
    edit_branch = source[edit_start:edit_end]

    assert "function shouldUseAgentChatForm(objectType) {" in source
    assert "return objectType === 'lead'" in source
    assert "|| objectType === 'message_template';" in source
    assert "if (shouldUseAgentChatForm(selection.object_type)) {" in edit_branch
    assert "sendAiMessageWithDisplay(`Edit ${label}`, `Manage ${selection.object_type} ${selection.ids[0]} edit`);" in edit_branch


def test_ai_agent_frontend_renders_open_record_feedback_before_workspace_fetch():
    source = Path("development/ai_agent/ui/frontend/static/js/ai_agent.js").read_text(encoding="utf-8")
    start = source.index("if (data.intent === 'OPEN_RECORD') {")
    end = source.index("if (data.intent === 'OPEN_FORM' && data.form?.fields && card) {", start)
    branch = source[start:end]

    assert "const preserveChatFocus = data.object_type === 'lead' || data.object_type === 'contact' || data.object_type === 'opportunity' || data.object_type === 'product' || data.object_type === 'asset' || data.object_type === 'brand' || data.object_type === 'model' || data.object_type === 'message_template';" in branch
    assert "if (preserveChatFocus && data.text) {" in branch
    assert "appendedMessage = appendChatMessage('agent', data.text" in branch
    assert "requestAnimationFrame(() => openAgentWorkspace(targetUrl, workspaceTitle, { preserveChatFocus }));" in branch
    assert branch.index("appendedMessage = appendChatMessage('agent', data.text") < branch.index("requestAnimationFrame(() => openAgentWorkspace(targetUrl, workspaceTitle, { preserveChatFocus }));")


def test_ai_agent_frontend_non_lead_open_record_behavior_remains_workspace_first():
    source = Path("development/ai_agent/ui/frontend/static/js/ai_agent.js").read_text(encoding="utf-8")
    start = source.index("if (data.intent === 'OPEN_RECORD') {")
    end = source.index("if (data.intent === 'OPEN_FORM' && data.form?.fields && card) {", start)
    branch = source[start:end]

    assert "if (preserveChatFocus) {" in branch
    assert "openAgentWorkspace(targetUrl, workspaceTitle);" in branch
    assert "if (!preserveChatFocus && data.text) {" in branch


def test_ai_agent_frontend_contact_open_record_now_uses_preserved_chat_focus():
    source = Path("development/ai_agent/ui/frontend/static/js/ai_agent.js").read_text(encoding="utf-8")
    start = source.index("if (data.intent === 'OPEN_RECORD') {")
    end = source.index("if (data.intent === 'OPEN_FORM' && data.form?.fields && card) {", start)
    branch = source[start:end]

    assert "data.object_type === 'contact'" in branch
    assert "requestAnimationFrame(() => openAgentWorkspace(targetUrl, workspaceTitle, { preserveChatFocus }));" in branch


def test_ai_agent_frontend_opportunity_open_record_now_uses_preserved_chat_focus():
    source = Path("development/ai_agent/ui/frontend/static/js/ai_agent.js").read_text(encoding="utf-8")
    start = source.index("if (data.intent === 'OPEN_RECORD') {")
    end = source.index("if (data.intent === 'OPEN_FORM' && data.form?.fields && card) {", start)
    branch = source[start:end]

    assert "data.object_type === 'opportunity'" in branch
    assert "requestAnimationFrame(() => openAgentWorkspace(targetUrl, workspaceTitle, { preserveChatFocus }));" in branch


def test_ai_agent_frontend_product_open_record_now_uses_preserved_chat_focus():
    source = Path("development/ai_agent/ui/frontend/static/js/ai_agent.js").read_text(encoding="utf-8")
    start = source.index("if (data.intent === 'OPEN_RECORD') {")
    end = source.index("if (data.intent === 'OPEN_FORM' && data.form?.fields && card) {", start)
    branch = source[start:end]

    assert "data.object_type === 'product'" in branch
    assert "requestAnimationFrame(() => openAgentWorkspace(targetUrl, workspaceTitle, { preserveChatFocus }));" in branch


def test_ai_agent_frontend_asset_open_record_now_uses_preserved_chat_focus():
    source = Path("development/ai_agent/ui/frontend/static/js/ai_agent.js").read_text(encoding="utf-8")
    start = source.index("if (data.intent === 'OPEN_RECORD') {")
    end = source.index("if (data.intent === 'OPEN_FORM' && data.form?.fields && card) {", start)
    branch = source[start:end]

    assert "data.object_type === 'asset'" in branch
    assert "requestAnimationFrame(() => openAgentWorkspace(targetUrl, workspaceTitle, { preserveChatFocus }));" in branch


def test_ai_agent_frontend_brand_open_record_now_uses_preserved_chat_focus():
    source = Path("development/ai_agent/ui/frontend/static/js/ai_agent.js").read_text(encoding="utf-8")
    start = source.index("if (data.intent === 'OPEN_RECORD') {")
    end = source.index("if (data.intent === 'OPEN_FORM' && data.form?.fields && card) {", start)
    branch = source[start:end]

    assert "data.object_type === 'brand'" in branch
    assert "requestAnimationFrame(() => openAgentWorkspace(targetUrl, workspaceTitle, { preserveChatFocus }));" in branch


def test_ai_agent_frontend_model_open_record_now_uses_preserved_chat_focus():
    source = Path("development/ai_agent/ui/frontend/static/js/ai_agent.js").read_text(encoding="utf-8")
    start = source.index("if (data.intent === 'OPEN_RECORD') {")
    end = source.index("if (data.intent === 'OPEN_FORM' && data.form?.fields && card) {", start)
    branch = source[start:end]

    assert "data.object_type === 'model'" in branch
    assert "requestAnimationFrame(() => openAgentWorkspace(targetUrl, workspaceTitle, { preserveChatFocus }));" in branch


def test_ai_agent_frontend_message_template_open_record_now_uses_preserved_chat_focus():
    source = Path("development/ai_agent/ui/frontend/static/js/ai_agent.js").read_text(encoding="utf-8")
    start = source.index("if (data.intent === 'OPEN_RECORD') {")
    end = source.index("if (data.intent === 'OPEN_FORM' && data.form?.fields && card) {", start)
    branch = source[start:end]

    assert "data.object_type === 'message_template'" in branch
    assert "requestAnimationFrame(() => openAgentWorkspace(targetUrl, workspaceTitle, { preserveChatFocus }));" in branch


def test_ai_agent_frontend_keeps_lead_contact_and_opportunity_submit_flow_in_chat_without_workspace_open():
    source = Path("development/ai_agent/ui/frontend/static/js/ai_agent.js").read_text(encoding="utf-8")
    start = source.index("async function submitAgentChatForm(event) {")
    end = source.index("function cancelAgentChatForm(", start)
    branch = source[start:end]

    assert "const skipWorkspaceOpen = data.object_type === 'lead' || data.object_type === 'contact' || data.object_type === 'opportunity';" in branch
    assert "const skipWorkspaceOpen = data.object_type === 'lead' || data.object_type === 'contact' || data.object_type === 'opportunity';" in branch
    assert "if (targetUrl && !skipWorkspaceOpen) {" in branch


def test_ai_agent_frontend_submit_branch_explicitly_includes_opportunity_in_no_auto_open_set():
    source = Path("development/ai_agent/ui/frontend/static/js/ai_agent.js").read_text(encoding="utf-8")
    start = source.index("async function submitAgentChatForm(event) {")
    end = source.index("function cancelAgentChatForm(", start)
    branch = source[start:end]

    assert "data.object_type === 'contact'" in branch
    assert "data.object_type === 'opportunity'" in branch
    assert "if (targetUrl && !skipWorkspaceOpen) {" in branch
    assert "requestAnimationFrame(() => openAgentWorkspace(targetUrl, workspaceTitle));" in branch


def test_ai_agent_frontend_lead_selection_open_still_routes_through_chat_paste():
    source = Path("development/ai_agent/ui/frontend/static/js/ai_agent.js").read_text(encoding="utf-8")
    start = source.index("function triggerSelectionOpen() {")
    end = source.index("function triggerSelectionEdit()", start)
    branch = source[start:end]

    assert "const shouldRouteThroughChatOpen = shouldUseAgentChatPaste(selection.object_type)" in branch
    assert "selection.object_type === 'contact'" in branch
    assert "selection.object_type === 'opportunity'" in branch
    assert "sendAiMessageWithDisplay(`Open ${label}`, `Manage ${selection.object_type} ${selection.ids[0]}`);" in branch


def test_ai_agent_frontend_contact_selection_open_now_routes_through_chat_first():
    source = Path("development/ai_agent/ui/frontend/static/js/ai_agent.js").read_text(encoding="utf-8")
    start = source.index("function triggerSelectionOpen() {")
    end = source.index("function triggerSelectionEdit()", start)
    branch = source[start:end]

    assert "selection.object_type === 'contact'" in branch
    assert "sendAiMessageWithDisplay(`Open ${label}`, `Manage ${selection.object_type} ${selection.ids[0]}`);" in branch


def test_ai_agent_frontend_opportunity_selection_open_now_routes_through_chat_first():
    source = Path("development/ai_agent/ui/frontend/static/js/ai_agent.js").read_text(encoding="utf-8")
    start = source.index("function triggerSelectionOpen() {")
    end = source.index("function triggerSelectionEdit()", start)
    branch = source[start:end]

    assert "selection.object_type === 'opportunity'" in branch
    assert "sendAiMessageWithDisplay(`Open ${label}`, `Manage ${selection.object_type} ${selection.ids[0]}`);" in branch


def test_ai_agent_frontend_product_selection_open_now_routes_through_chat_first():
    source = Path("development/ai_agent/ui/frontend/static/js/ai_agent.js").read_text(encoding="utf-8")
    start = source.index("function triggerSelectionOpen() {")
    end = source.index("function triggerSelectionEdit()", start)
    branch = source[start:end]

    assert "selection.object_type === 'product'" in branch
    assert "sendAiMessageWithDisplay(`Open ${label}`, `Manage ${selection.object_type} ${selection.ids[0]}`);" in branch


def test_ai_agent_frontend_asset_selection_open_now_routes_through_chat_first():
    source = Path("development/ai_agent/ui/frontend/static/js/ai_agent.js").read_text(encoding="utf-8")
    start = source.index("function triggerSelectionOpen() {")
    end = source.index("function triggerSelectionEdit()", start)
    branch = source[start:end]

    assert "selection.object_type === 'asset'" in branch
    assert "sendAiMessageWithDisplay(`Open ${label}`, `Manage ${selection.object_type} ${selection.ids[0]}`);" in branch


def test_ai_agent_frontend_brand_selection_open_now_routes_through_chat_first():
    source = Path("development/ai_agent/ui/frontend/static/js/ai_agent.js").read_text(encoding="utf-8")
    start = source.index("function triggerSelectionOpen() {")
    end = source.index("function triggerSelectionEdit()", start)
    branch = source[start:end]

    assert "selection.object_type === 'brand'" in branch
    assert "sendAiMessageWithDisplay(`Open ${label}`, `Manage ${selection.object_type} ${selection.ids[0]}`);" in branch


def test_ai_agent_frontend_model_selection_open_now_routes_through_chat_first():
    source = Path("development/ai_agent/ui/frontend/static/js/ai_agent.js").read_text(encoding="utf-8")
    start = source.index("function triggerSelectionOpen() {")
    end = source.index("function triggerSelectionEdit()", start)
    branch = source[start:end]

    assert "selection.object_type === 'model'" in branch
    assert "sendAiMessageWithDisplay(`Open ${label}`, `Manage ${selection.object_type} ${selection.ids[0]}`);" in branch


def test_ai_agent_frontend_message_template_selection_open_now_routes_through_chat_first():
    source = Path("development/ai_agent/ui/frontend/static/js/ai_agent.js").read_text(encoding="utf-8")
    start = source.index("function triggerSelectionOpen() {")
    end = source.index("function triggerSelectionEdit()", start)
    branch = source[start:end]

    assert "selection.object_type === 'message_template'" in branch
    assert "sendAiMessageWithDisplay(`Open ${label}`, `Manage ${selection.object_type} ${selection.ids[0]}`);" in branch


def test_ai_agent_frontend_asset_card_open_record_uses_display_first_chat_routing():
    source = Path("development/ai_agent/ui/frontend/static/js/ai_agent.js").read_text(encoding="utf-8")
    start = source.index("function renderAgentChatCard(card) {")
    end = source.index("function triggerLeadCardSendMessage(", start)
    branch = source[start:end]

    assert "card.actions.filter(act => act.action !== 'open')" in branch
    assert "sendAiMessageWithDisplay('Edit ${escapeAgentHtml(displayName)}'" in branch


def test_ai_agent_frontend_brand_card_open_record_uses_display_first_chat_routing():
    source = Path("development/ai_agent/ui/frontend/static/js/ai_agent.js").read_text(encoding="utf-8")
    start = source.index("function renderAgentChatCard(card) {")
    end = source.index("function triggerLeadCardSendMessage(", start)
    branch = source[start:end]

    assert "objectType = card.object_type" in branch
    assert "card.actions.filter(act => act.action !== 'open')" in branch


def test_ai_agent_frontend_model_card_open_record_uses_display_first_chat_routing():
    source = Path("development/ai_agent/ui/frontend/static/js/ai_agent.js").read_text(encoding="utf-8")
    start = source.index("function renderAgentChatCard(card) {")
    end = source.index("function triggerLeadCardSendMessage(", start)
    branch = source[start:end]

    assert "objectType = card.object_type" in branch
    assert "card.actions.filter(act => act.action !== 'open')" in branch


def test_ai_agent_frontend_message_template_card_uses_preview_and_send_handoff_actions():
    source = Path("development/ai_agent/ui/frontend/static/js/ai_agent.js").read_text(encoding="utf-8")
    start = source.index("function renderAgentChatCard(card) {")
    end = source.index("function triggerLeadCardSendMessage(", start)
    branch = source[start:end]

    assert "if (act.action === 'preview_image' && act.url) {" in branch
    assert "openAgentImagePreview" in branch
    assert "if (act.action === 'use_in_send') {" in branch
    assert "startTemplateSendFromAgent" in branch


def test_ai_agent_frontend_send_message_handoff_appends_chat_feedback_before_workspace_open():
    source = Path("development/ai_agent/ui/frontend/static/js/ai_agent.js").read_text(encoding="utf-8")
    start = source.index("function completeAgentSendMessageHandoff(")
    end = source.index("function startTemplateSendFromAgent(", start)
    branch = source[start:end]

    assert "appendedMessage = appendChatMessage('agent', messageText);" in branch
    assert "requestAnimationFrame(() => openAgentWorkspace(redirectUrl, 'Send Message', { preserveChatFocus: true }));" in branch
    assert branch.index("appendedMessage = appendChatMessage('agent', messageText);") < branch.index("requestAnimationFrame(() => openAgentWorkspace(redirectUrl, 'Send Message', { preserveChatFocus: true }));")


def test_ai_agent_frontend_send_message_handoff_preserves_selection_and_template_session_state():
    source = Path("development/ai_agent/ui/frontend/static/js/ai_agent.js").read_text(encoding="utf-8")
    start = source.index("function completeAgentSendMessageHandoff(")
    end = source.index("function startTemplateSendFromAgent(", start)
    branch = source[start:end]

    assert "sessionStorage.setItem('aiAgentMessageSelection', JSON.stringify(selection));" in branch
    assert "sessionStorage.setItem('aiAgentMessageTemplate', templateId);" in branch
    assert "sessionStorage.removeItem('aiAgentMessageTemplate');" in branch


def test_ai_agent_frontend_send_message_intent_uses_ai_native_composer():
    source = Path("development/ai_agent/ui/frontend/static/js/ai_agent.js").read_text(encoding="utf-8")
    start = source.index("if (data.intent === 'SEND_MESSAGE') {")
    end = source.index("if (data.intent === 'OPEN_FORM' && data.form?.fields) {", start)
    branch = source[start:end]

    assert "appendAgentSendMessageComposer(" in branch
    assert "redirectUrl: data.redirect_url" in branch
    assert "templateId: data.template_id" in branch
    assert "selection: data.selection" in branch


def test_ai_agent_frontend_non_contact_non_opportunity_selection_open_can_still_use_workspace_route():
    source = Path("development/ai_agent/ui/frontend/static/js/ai_agent.js").read_text(encoding="utf-8")
    start = source.index("function triggerSelectionOpen() {")
    end = source.index("function triggerSelectionEdit()", start)
    branch = source[start:end]

    assert "const url = getAgentObjectRoute(selection.object_type, selection.ids[0], 'detail');" in branch
    assert "openAgentWorkspace(url, `${label}`);" in branch


def test_ai_agent_frontend_scrolls_prompt_triggered_actions_into_latest_chat_area():
    source = Path("development/ai_agent/ui/frontend/static/js/ai_agent.js").read_text(encoding="utf-8")

    assert "function scrollAgentChatMessageIntoView(target) {" in source
    assert "appendChatMessage('user', displayText);" in source


def test_ai_agent_frontend_card_delete_confirmation_scrolls_latest_chat_area_into_view():
    source = Path("development/ai_agent/ui/frontend/static/js/ai_agent.js").read_text(encoding="utf-8")
    start = source.index("function triggerSnapshotDelete(objectType, recordId, displayName) {")
    end = source.index("function shouldUseAgentChatPaste(objectType) {", start)
    branch = source[start:end]

    assert "appendChatMessage('agent', `Are you sure you want to delete **${displayName}**?\\n[Yes] [Cancel]\\n<!--delete-confirm|${objectType}|${recordId}|${displayName}-->`);" in branch


def test_ai_agent_frontend_selection_delete_confirmation_scrolls_latest_chat_area_into_view():
    source = Path("development/ai_agent/ui/frontend/static/js/ai_agent.js").read_text(encoding="utf-8")
    start = source.index("function triggerSelectionDelete() {")
    end = source.index("function selectAgentRecord(recordId, objectType, row) {", start)
    branch = source[start:end]

    assert "appendChatMessage('agent', `Are you sure you want to delete ${subject}?\\n[Yes] [Cancel]`);" in branch


def test_ai_agent_frontend_renders_and_initializes_lead_lookup_controls():
    source = Path("development/ai_agent/ui/frontend/static/js/ai_agent.js").read_text(encoding="utf-8")

    assert "if (field.control === 'lookup') {" in source
    assert "class=\"agent-chat-lookup-id\"" in source
    assert "agent-chat-lookup-input" in source
    assert "agent-chat-lookup-clear" in source
    assert "function initAgentChatLookupFields(root) {" in source
    assert "fetch(`/lookups/search?q=${encodeURIComponent(query || '')}&type=${encodeURIComponent(lookupObject)}`)" in source


def test_ai_agent_frontend_initializes_lookup_controls_on_render_and_validation_refresh():
    source = Path("development/ai_agent/ui/frontend/static/js/ai_agent.js").read_text(encoding="utf-8")

    assert "initAgentChatLookupFields(msgDiv);" in source
    assert "initAgentChatLookupFields(replacementCard);" in source
