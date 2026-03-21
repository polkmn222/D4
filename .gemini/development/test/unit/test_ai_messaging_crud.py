import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import patch, AsyncMock

from db.database import Base
from ai_agent.backend.service import AiAgentService
from db.models import MessageTemplate, MessageSend, Contact

SQLALCHEMY_DATABASE_URL = "sqlite:///./db/test_runs/test_ai_messaging_crud.db"
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


@pytest.mark.asyncio
async def test_ai_message_template_crud_flow(db):
    mock_create_template = {
        "intent": "CREATE",
        "object_type": "message_template",
        "data": {"name": "Welcome SMS", "subject": "Welcome", "content": "Hello, welcome!"},
        "text": "Creating template.",
        "score": 1.0,
    }
    with patch.object(AiAgentService, "_call_multi_llm_ensemble", new_callable=AsyncMock) as mock_ensemble:
        mock_ensemble.return_value = mock_create_template
        res = await AiAgentService.process_query(db, "Create template Welcome SMS with content Hello, welcome!")
        assert "Success! Created Template" in res["text"]
        template = db.query(MessageTemplate).filter(MessageTemplate.name == "Welcome SMS").first()
        assert template is not None
        template_id = template.id

    mock_query_template = {
        "intent": "QUERY",
        "object_type": "message_template",
        "sql": f"SELECT id, name, subject FROM message_templates WHERE id = '{template_id}'",
        "text": "Found the template.",
        "score": 1.0,
    }
    with patch.object(AiAgentService, "_call_multi_llm_ensemble", new_callable=AsyncMock) as mock_ensemble:
        mock_ensemble.return_value = mock_query_template
        res = await AiAgentService.process_query(db, f"Show me template {template_id}")
        assert len(res["results"]) > 0
        assert res["results"][0]["name"] == "Welcome SMS"

    mock_update_template = {
        "intent": "UPDATE",
        "object_type": "message_template",
        "record_id": template_id,
        "data": {"content": "Updated welcome message."},
        "text": "Updating template content.",
        "score": 1.0,
    }
    with patch.object(AiAgentService, "_call_multi_llm_ensemble", new_callable=AsyncMock) as mock_ensemble:
        mock_ensemble.return_value = mock_update_template
        res = await AiAgentService.process_query(db, f"Update template {template_id} content to Updated welcome message.")
        assert "Success! Updated Template" in res["text"]
        db.refresh(template)
        assert template.content == "Updated welcome message."

    mock_delete_template = {
        "intent": "DELETE",
        "object_type": "message_template",
        "record_id": template_id,
        "text": "Deleting template.",
        "score": 1.0,
    }
    with patch.object(AiAgentService, "_call_multi_llm_ensemble", new_callable=AsyncMock) as mock_ensemble:
        mock_ensemble.return_value = mock_delete_template
        res = await AiAgentService.process_query(db, f"Delete template {template_id}")
        assert "Success! Deleted Template" in res["text"]
        deleted_template = db.query(MessageTemplate).filter(MessageTemplate.id == template_id).first()
        assert deleted_template is not None
        assert deleted_template.deleted_at is not None


@pytest.mark.asyncio
async def test_ai_message_send_query(db):
    contact = Contact(id="CNT-001", first_name="Jane", last_name="Doe", email="jane@example.com")
    template = MessageTemplate(id="MT-001", name="Test Temp", subject="Hi", content="Test content")
    db.add_all([contact, template])
    db.commit()

    msg_send = MessageSend(
        id="MS-001",
        contact=contact.id,
        template=template.id,
        content="Test message",
        direction="Outbound",
        status="Sent",
    )
    db.add(msg_send)
    db.commit()

    mock_query_message = {
        "intent": "QUERY",
        "object_type": "message_send",
        "sql": f"SELECT id, contact, template, status, sent_at FROM message_sends WHERE id = '{msg_send.id}'",
        "text": "Found the message.",
        "score": 1.0,
    }
    with patch.object(AiAgentService, "_call_multi_llm_ensemble", new_callable=AsyncMock) as mock_ensemble:
        mock_ensemble.return_value = mock_query_message
        res = await AiAgentService.process_query(db, f"Show me message {msg_send.id}")
        assert len(res["results"]) > 0
        assert res["results"][0]["status"] == "Sent"

    mock_query_messages_by_contact = {
        "intent": "QUERY",
        "object_type": "message_send",
        "sql": f"SELECT id, contact, template, status, sent_at FROM message_sends WHERE contact = '{contact.id}'",
        "text": "Found messages for contact.",
        "score": 1.0,
    }
    with patch.object(AiAgentService, "_call_multi_llm_ensemble", new_callable=AsyncMock) as mock_ensemble:
        mock_ensemble.return_value = mock_query_messages_by_contact
        res = await AiAgentService.process_query(db, f"Show me messages for contact {contact.id}")
        assert len(res["results"]) > 0
        assert res["results"][0]["contact"] == contact.id
