import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from db.database import Base
from db.models import Opportunity, Contact, Model, VehicleSpecification
from backend.app.services.opportunity_service import OpportunityService
from datetime import datetime, timedelta

# Use in-memory SQLite for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture
def db():
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    yield session
    session.close()
    Base.metadata.drop_all(bind=engine)

def test_ai_recommendations_model_filter(db):
    # 1. Setup Data
    # Contact with phone
    c1 = Contact(id="C1", first_name="John", last_name="Doe", name="John Doe", phone="01012345678")
    db.add(c1)
    
    # Brand and Model
    brand = VehicleSpecification(id="B1", name="Brand A", record_type="Brand")
    mod = Model(id="M1", name="Model X", brand="B1")
    db.add(brand)
    db.add(mod)
    
    # Opportunity WITH Model (Hot - Test Drive)
    o1 = Opportunity(id="O1", contact="C1", name="Opp With Model", stage="Test Drive", model="M1", created_at=datetime.utcnow())
    
    # Opportunity WITHOUT Model (Hot - Test Drive)
    o2 = Opportunity(id="O2", contact="C1", name="Opp Without Model", stage="Test Drive", model=None, created_at=datetime.utcnow())
    
    db.add(o1)
    db.add(o2)
    db.commit()
    
    # 2. Run Service
    recommendations = OpportunityService.get_ai_recommendations(db)
    
    # 3. Assertions
    # Should only find O1 because O2 has no model
    assert len(recommendations) == 1
    assert recommendations[0].id == "O1"
    assert recommendations[0].name == "Opp With Model"
    
    print("\n[TEST SUCCESS] AI Recommendations correctly filtered out Opportunity without a Model.")

def test_ai_recommendations_phone_filter(db):
    # 1. Setup Data
    brand = VehicleSpecification(id="B1", name="Brand A", record_type="Brand")
    mod = Model(id="M1", name="Model X", brand="B1")
    db.add(brand)
    db.add(mod)
    
    # Contact WITHOUT phone
    c2 = Contact(id="C2", first_name="No", last_name="Phone", name="No Phone", phone="")
    db.add(c2)
    
    # Opportunity WITH Model but Contact has NO phone
    o3 = Opportunity(id="O3", contact="C2", name="Opp No Phone", stage="Test Drive", model="M1", created_at=datetime.utcnow())
    db.add(o3)
    db.commit()
    
    # 2. Run Service
    recommendations = OpportunityService.get_ai_recommendations(db)
    
    # 3. Assertions
    assert len(recommendations) == 0
    
    print("[TEST SUCCESS] AI Recommendations correctly filtered out Contact without a phone number.")
