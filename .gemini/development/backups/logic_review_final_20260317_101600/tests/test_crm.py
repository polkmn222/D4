import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.app.database import Base
from backend.app.models import Account, Lead, Opportunity
from backend.app.services.lead_service import LeadService
from backend.app.services.account_service import AccountService
from backend.app.utils.sf_id import get_id

# Setup test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture
def db():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

def test_sf_id_generation():
    account_id = get_id("Account")
    assert len(account_id) == 18
    assert account_id.startswith("001")
    
    opp_id = get_id("Opportunity")
    assert len(opp_id) == 18
    assert opp_id.startswith("006")

def test_lead_conversion(db):
    # 1. Create a Lead (Company removed in Phase 10)
    lead = LeadService.create_lead(
        db, first_name="John", last_name="Doe", 
        email="john@tesla.com", gender="Male"
    )
    assert lead.id.startswith("00Q")
    
    # 2. Convert Lead
    LeadService.convert_lead(db, lead.id)
    
    # 3. Verify Account and Opportunity
    account = db.query(Account).filter(Account.name == "John Doe").first()
    assert account is not None
    assert account.id.startswith("001")
    assert account.record_type == "Individual"
    
    opp = db.query(Opportunity).filter(Opportunity.account == account.id).first()
    assert opp is not None
    assert opp.id.startswith("006")
