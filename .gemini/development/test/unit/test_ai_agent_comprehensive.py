import pytest
import os
import json
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import patch, MagicMock, AsyncMock

from db.database import Base
from ai_agent.backend.service import AiAgentService as AiAgentService
from db.models import Lead, Contact, Opportunity, VehicleSpecification, Model, Product, Asset, Task, MessageTemplate, MessageSend

# Setup Test Database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_ai_agent_comprehensive.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="module")
def db():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    yield db
    db.close()
    Base.metadata.drop_all(bind=engine)
    if os.path.exists("./test_ai_agent_comprehensive.db"):
        os.remove("./test_ai_agent_comprehensive.db")

@pytest.mark.asyncio
async def test_phase1_metadata():
    """Verify metadata.json exists and is valid."""
    path = os.path.join(os.getcwd(), ".gemini", "skills", "backend", "metadata.json")
    assert os.path.exists(path)
    with open(path, "r") as f:
        data = json.load(f)
        assert "tables" in data
        assert "leads" in data["tables"]
        assert "contacts" in data["tables"]

@pytest.mark.asyncio
@patch("ai_agent.backend.service.AiAgentService._call_llm")
async def test_phase2_lead_crud(mock_llm, db):
    """Test Lead CRUD via AI Agent."""
    # Test Create
    mock_llm.return_value = json.dumps({
        "intent": "CREATE", 
        "text": "Creating lead...", 
        "data": {"first_name": "John", "last_name": "Wick", "phone": "010-1234-5678"}, 
        "object_type": "lead"
    })
    res = await AiAgentService.process_query(db, "Create a lead for John Wick")
    assert res["intent"] == "CREATE"
    lead = db.query(Lead).filter(Lead.last_name == "Wick").first()
    assert lead is not None
    assert lead.first_name == "John"

    # Test Query
    mock_llm.return_value = json.dumps({
        "intent": "QUERY", 
        "text": "Searching...", 
        "sql": "SELECT * FROM leads WHERE last_name = 'Wick' AND deleted_at IS NULL", 
        "object_type": "lead"
    })
    res = await AiAgentService.process_query(db, "Find lead Wick")
    assert len(res["results"]) > 0
    assert res["results"][0]["last_name"] == "Wick"

@pytest.mark.asyncio
@patch("ai_agent.backend.service.AiAgentService._call_llm")
async def test_phase3_contact_crud(mock_llm, db):
    """Test Contact CRUD."""
    mock_llm.return_value = json.dumps({
        "intent": "CREATE", 
        "data": {"first_name": "Tony", "last_name": "Stark", "email": "tony@stark.com"}, 
        "object_type": "contact"
    })
    await AiAgentService.process_query(db, "Create contact Tony Stark")
    contact = db.query(Contact).filter(Contact.last_name == "Stark").first()
    assert contact is not None

@pytest.mark.asyncio
@patch("ai_agent.backend.service.AiAgentService._call_llm")
async def test_phase4_opportunity_crud(mock_llm, db):
    """Test Opportunity CRUD."""
    mock_llm.return_value = json.dumps({
        "intent": "CREATE", 
        "data": {"name": "Big Deal", "amount": 50000000}, 
        "object_type": "opportunity"
    })
    await AiAgentService.process_query(db, "Create an opportunity Big Deal for 50M")
    opp = db.query(Opportunity).filter(Opportunity.name == "Big Deal").first()
    assert opp is not None

@pytest.mark.asyncio
@patch("ai_agent.backend.service.AiAgentService._call_llm")
async def test_phase5_master_and_task(mock_llm, db):
    """Test Brands, Models, and Tasks."""
    # Test Brand
    mock_llm.return_value = json.dumps({
        "intent": "CREATE", 
        "data": {"name": "Tesla", "record_type": "Brand"}, 
        "object_type": "vehicle_specification"
    })
    await AiAgentService.process_query(db, "Create brand Tesla")
    brand = db.query(VehicleSpecification).filter(VehicleSpecification.name == "Tesla").first()
    assert brand is not None

    # Test Task
    mock_llm.return_value = json.dumps({
        "intent": "CREATE", 
        "data": {"subject": "Follow up with Tesla"}, 
        "object_type": "task"
    })
    await AiAgentService.process_query(db, "Remind me to follow up")
    task = db.query(Task).filter(Task.subject == "Follow up with Tesla").first()
    assert task is not None

@pytest.mark.asyncio
@patch("ai_agent.backend.service.AiAgentService._call_llm")
async def test_phase6_chat_and_inventory(mock_llm, db):
    """Test CHAT intent and Product/Asset CRUD."""
    # Test Greeting (CHAT)
    mock_llm.return_value = json.dumps({
        "intent": "CHAT", 
        "text": "Hello! I am your AI Agent."
    })
    res = await AiAgentService.process_query(db, "Hi")
    assert res["intent"] == "CHAT"
    assert "Hello" in res["text"]

    # Test Product
    mock_llm.return_value = json.dumps({
        "intent": "CREATE", 
        "data": {"name": "Battery Pack", "category": "Parts"}, 
        "object_type": "product"
    })
    await AiAgentService.process_query(db, "Add product Battery Pack")
    prod = db.query(Product).filter(Product.name == "Battery Pack").first()
    assert prod is not None

@pytest.mark.asyncio
@patch("ai_agent.backend.service.AiAgentService._call_llm")
async def test_phase7_messaging_data(mock_llm, db):
    """Test Template and Message Log CRUD."""
    # Test Template
    mock_llm.return_value = json.dumps({
        "intent": "CREATE", 
        "data": {"name": "Template A", "content": "Hello World"}, 
        "object_type": "message_template"
    })
    await AiAgentService.process_query(db, "Create template A")
    temp = db.query(MessageTemplate).filter(MessageTemplate.name == "Template A").first()
    assert temp is not None

@pytest.mark.asyncio
@patch("ai_agent.backend.service.AiAgentService._call_llm")
@patch("backend.app.services.messaging_service.MessagingService.bulk_send")
async def test_phase8_realtime_messaging(mock_bulk, mock_llm, db):
    """Test real-time message sending."""
    mock_bulk.return_value = 1
    mock_llm.return_value = json.dumps({
        "intent": "MESSAGE", 
        "text": "Sending...", 
        "data": {"contact_ids": ["003test"], "content": "Hi", "record_type": "SMS"}
    })
    res = await AiAgentService.process_query(db, "Send message to 003test")
    assert res["intent"] == "MESSAGE"
    mock_bulk.assert_called_once()

@pytest.mark.asyncio
@patch("ai_agent.backend.service.AiAgentService._call_llm")
async def test_fuzzy_logic_and_fallback(mock_llm, db):
    """Test 'opp' abbreviation and out-of-scope fallback."""
    # Test 'opp' abbreviation
    mock_llm.return_value = json.dumps({
        "intent": "QUERY", 
        "sql": "SELECT * FROM opportunities WHERE deleted_at IS NULL", 
        "object_type": "opportunity"
    })
    res = await AiAgentService.process_query(db, "show me opps")
    assert res["object_type"] == "opportunity"

    # Test Out of Scope
    mock_llm.return_value = json.dumps({
        "intent": "CHAT", 
        "text": "I’m afraid I can’t help with that specific request, but I can assist you with something else. Thank you."
    })
    res = await AiAgentService.process_query(db, "Who is the president?")
    assert "I’m afraid I can’t help" in res["text"]
