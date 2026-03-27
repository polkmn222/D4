import pytest
from unittest.mock import patch

from ai_agent.llm.backend.recommendations import AIRecommendationService
from web.backend.app.services.opportunity_service import OpportunityService
from web.backend.app.services.contact_service import ContactService
from web.backend.app.services.model_service import ModelService
from web.backend.app.services.vehicle_spec_service import VehicleSpecService


pytestmark = pytest.mark.integration


def test_refresh_opportunity_temperatures(db):
    opp_hot = OpportunityService.create_opportunity(db, name="Hot Opp", stage="Test Drive")
    opp_cold = OpportunityService.create_opportunity(db, name="Cold Opp", stage="Closed Lost")

    with patch.object(AIRecommendationService, "_already_refreshed_today", return_value=False):
        AIRecommendationService.refresh_opportunity_temperatures(db)

    db.refresh(opp_hot)
    db.refresh(opp_cold)

    assert opp_hot.temperature == "Hot"
    assert opp_cold.temperature == "Cold"

    OpportunityService.delete_opportunity(db, opp_hot.id)
    OpportunityService.delete_opportunity(db, opp_cold.id)


def test_get_ai_recommendations_hot_deals(db):
    contact = ContactService.create_contact(db, first_name="Rec", last_name="Tester", phone="010-1234-5678")
    brand = VehicleSpecService.create_spec(db, name="Test Brand", record_type="Brand")
    model = ModelService.create_model(db, name="Test Model", brand=brand.id)
    opp = OpportunityService.create_opportunity(db, name="Hot Deal Opp", contact=contact.id, model=model.id, stage="Test Drive")

    recommendations = AIRecommendationService.get_ai_recommendations(db, mode="Hot Deals")

    assert any(o.id == opp.id for o in recommendations)

    OpportunityService.delete_opportunity(db, opp.id)
    ModelService.delete_model(db, model.id)
    VehicleSpecService.delete_vehicle_spec(db, brand.id)
    ContactService.delete_contact(db, contact.id)


def test_get_sendable_recommendations(db):
    contact = ContactService.create_contact(db, first_name="Sendable", last_name="Tester", phone="010-9999-9999")
    brand = VehicleSpecService.create_spec(db, name="Brand2", record_type="Brand")
    model = ModelService.create_model(db, name="Model2", brand=brand.id)
    opp = OpportunityService.create_opportunity(db, name="Sendable Opp", contact=contact.id, model=model.id, stage="Test Drive")

    sendable = AIRecommendationService.get_sendable_recommendations(db)

    assert any(o.id == opp.id for o in sendable)

    OpportunityService.delete_opportunity(db, opp.id)
    ModelService.delete_model(db, model.id)
    VehicleSpecService.delete_vehicle_spec(db, brand.id)
    ContactService.delete_contact(db, contact.id)
