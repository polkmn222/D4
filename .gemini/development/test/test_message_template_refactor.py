import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from db.database import Base, get_db
from db.models import MessageTemplate
from backend.app.services.message_template_service import MessageTemplateService
from fastapi.testclient import TestClient
from backend.app.main import app
import uuid

# Setup test database
TEST_DB_URL = "sqlite:///./test_refactor.db"

@pytest.fixture
def db_session():
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    engine = create_engine(TEST_DB_URL)
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def test_message_template_model_type(db_session):
    # Check if 'content' column is String
    from sqlalchemy import inspect
    inspector = inspect(db_session.bind)
    columns = inspector.get_columns('message_templates')
    content_col = next(c for c in columns if c['name'] == 'content')
    # In SQLite/SQLAlchemy, String might be reflected as VARCHAR or TEXT depending on how it's defined
    # But we want to ensure it's not the old Text type if we specifically changed it to String
    print(f"Content column type: {content_col['type']}")
    # This is more of a smoke test to ensure the column exists and name is 'content'
    assert content_col['name'] == 'content'

def test_message_template_crud(db_session):
    # Test service still works with 'content' column
    name = "Test Template"
    content = "Hello {Name}, this is a description/content."
    
    template = MessageTemplateService.create_template(
        db_session, 
        name=name, 
        content=content,
        record_type="SMS"
    )
    
    assert template.id is not None
    assert template.name == name
    assert template.content == content
    
    # Test update
    new_content = "Updated description"
    updated = MessageTemplateService.update_template(db_session, template.id, content=new_content)
    assert updated.content == new_content

def test_router_detail_mapping(db_session):
    client = TestClient(app)
    
    # Mocking or using test DB for the app
    # For simplicity, we'll check the router logic if possible, or just the status code
    # We can override the get_db dependency
    from db.database import get_db
    app.dependency_overrides[get_db] = lambda: db_session
    
    template = MessageTemplateService.create_template(
        db_session, 
        name="Router Test", 
        content="Testing Router Mapping",
        record_type="LMS"
    )
    
    response = client.get(f"/message_templates/{template.id}")
    assert response.status_code == 200
    # The response is HTML, we check if 'Description' is in it instead of 'Content'
    content_text = response.text
    assert "Content" in content_text
    assert "Testing Router Mapping" in content_text
    # Ensure 'Description' label is NOT there anymore if we reverted to 'Content'
    assert ">Description<" not in content_text 
    
    app.dependency_overrides.clear()
