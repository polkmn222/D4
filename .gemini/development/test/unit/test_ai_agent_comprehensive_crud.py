import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import patch, AsyncMock
from pathlib import Path

from db.database import Base
from ai_agent.backend.service import AiAgentService
from db.models import Lead, Contact, Opportunity, Asset, Product, VehicleSpecification, Model, MessageTemplate

# Setup Test Database
TEST_DB_PATH = Path(__file__).resolve().parents[1] / "databases" / "test_ai_comprehensive_crud.db"
SQLALCHEMY_DATABASE_URL = f"sqlite:///{TEST_DB_PATH}"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture
def db():
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)

async def run_crud_test(db, obj_type, create_data, update_data, search_query):
    """Generic helper to test CRUD for any object type."""
    
    # 1. CREATE
    mock_create = {
        "intent": "CREATE",
        "object_type": obj_type,
        "data": create_data,
        "text": f"Creating {obj_type}.",
        "score": 1.0
    }
    with patch.object(AiAgentService, '_call_multi_llm_ensemble', new_callable=AsyncMock) as mock_ensemble:
        mock_ensemble.return_value = mock_create
        res = await AiAgentService.process_query(db, f"Create {obj_type}")
        assert "Success" in res["text"]
        
    # Get ID from DB
    if obj_type == "brand":
        record = db.query(VehicleSpecification).first()
    elif obj_type == "message_template":
        record = db.query(MessageTemplate).first()
    elif obj_type == "lead":
        record = db.query(Lead).first()
    elif obj_type == "contact":
        record = db.query(Contact).first()
    elif obj_type == "opportunity":
        record = db.query(Opportunity).first()
    elif obj_type == "asset":
        record = db.query(Asset).first()
    elif obj_type == "product":
        record = db.query(Product).first()
    elif obj_type == "model":
        record = db.query(Model).first()
    else:
        pytest.fail(f"Unsupported object type in test: {obj_type}")
    
    assert record is not None
    record_id = record.id

    # 2. READ (QUERY)
    mock_query = {
        "intent": "QUERY",
        "object_type": obj_type,
        "sql": f"SELECT * FROM {record.__tablename__} WHERE id = '{record_id}'",
        "text": f"Found {obj_type}.",
        "score": 1.0
    }
    with patch.object(AiAgentService, '_call_multi_llm_ensemble', new_callable=AsyncMock) as mock_ensemble:
        mock_ensemble.return_value = mock_query
        res = await AiAgentService.process_query(db, search_query)
        assert len(res["results"]) > 0

    # 3. UPDATE
    mock_update = {
        "intent": "UPDATE",
        "object_type": obj_type,
        "record_id": record_id,
        "data": update_data,
        "text": f"Updating {obj_type}.",
        "score": 1.0
    }
    with patch.object(AiAgentService, '_call_multi_llm_ensemble', new_callable=AsyncMock) as mock_ensemble:
        mock_ensemble.return_value = mock_update
        res = await AiAgentService.process_query(db, f"Update {obj_type} {record_id}")
        assert "Success" in res["text"]
        
    # 4. DELETE
    mock_delete = {
        "intent": "DELETE",
        "object_type": obj_type,
        "record_id": record_id,
        "text": f"Deleting {obj_type}.",
        "score": 1.0
    }
    with patch.object(AiAgentService, '_call_multi_llm_ensemble', new_callable=AsyncMock) as mock_ensemble:
        mock_ensemble.return_value = mock_delete
        res = await AiAgentService.process_query(db, f"Delete {obj_type} {record_id}")
        assert "Success" in res["text"]
        
        db.refresh(record)
        assert record.deleted_at is not None

@pytest.mark.asyncio
async def test_all_objects_crud(db):
    # Test cases for each object
    test_cases = [
        ("lead", {"last_name": "TestLead", "status": "New"}, {"status": "Qualified"}, "Show me TestLead"),
        ("contact", {"last_name": "TestContact", "email": "c@test.com"}, {"phone": "123"}, "Find TestContact"),
        ("opportunity", {"name": "TestOpp", "amount": 100}, {"amount": 200}, "Show TestOpp"),
        ("brand", {"name": "TestBrand", "record_type": "Brand"}, {"name": "UpdatedBrand"}, "Search TestBrand"),
        ("model", {"name": "TestModel"}, {"description": "Nice car"}, "Find TestModel"),
        ("product", {"name": "TestProduct"}, {"base_price": 500}, "List TestProduct"),
        ("asset", {"vin": "TESTVIN123"}, {"status": "Sold"}, "Show VIN TESTVIN123"),
        ("message_template", {"name": "TestTemp", "content": "Hi"}, {"subject": "Hello"}, "Show TestTemp"),
    ]
    
    for obj_type, c_data, u_data, s_query in test_cases:
        print(f"Testing CRUD for: {obj_type}")
        await run_crud_test(db, obj_type, c_data, u_data, s_query)
