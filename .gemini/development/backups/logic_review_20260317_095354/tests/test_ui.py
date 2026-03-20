from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.services.contact_service import init_db

def test_dashboard_route():
    init_db() # Ensure tables are created for the test context
    with TestClient(app) as client:
        response = client.get("/")
        assert response.status_code == 200
        assert "Contacts" in response.text
        assert "AI Ready CRM" in response.text

def test_static_css_load():
    with TestClient(app) as client:
        response = client.get("/static/css/style.css")
        assert response.status_code == 200
        assert "Salesforce Blue" in response.text
