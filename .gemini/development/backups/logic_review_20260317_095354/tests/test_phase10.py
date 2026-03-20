import pytest
from sqlalchemy.orm import Session
from backend.app.database import Base, engine, SessionLocal
from backend.app.models import Lead, Campaign, VehicleSpecification, Account
from backend.app.services.lead_service import LeadService
from backend.app.services.campaign_service import CampaignService
from backend.app.services.vehicle_spec_service import VehicleSpecService
import time

@pytest.fixture
def db():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def test_auto_timestamps(db):
    # 1. Create a Campaign
    camp = CampaignService.create_campaign(db, name="Big Sale")
    assert camp.created_at is not None
    initial_updated = camp.updated_at
    
    # Wait a bit
    time.sleep(1)
    
    # 2. Update it
    camp.status = "Completed"
    db.commit()
    db.refresh(camp)
    
    assert camp.updated_at > initial_updated

def test_vehicle_spec_and_lookups(db):
    # 1. Create Brand
    brand = VehicleSpecService.create_spec(db, name="Solaris", record_type="Brand")
    
    # 2. Create Campaign
    camp = CampaignService.create_campaign(db, name="Launch Campaign")
    
    # 3. Create Lead with Lookups
    lead = LeadService.create_lead(
        db, 
        first_name="Automotive", 
        last_name="Tester", 
        email="test@auto.com",
        gender="Male",
        campaign_id=camp.id,
        brand_id=brand.id,
        status="New"
    )
    
    assert lead.brand_id == brand.id
    assert lead.campaign_id == camp.id
    assert lead.gender == "Male"
    assert lead.status == "New"
