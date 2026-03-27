from fastapi.testclient import TestClient

from agent.ui.backend.main import app


client = TestClient(app)


def test_bootstrap_endpoint_returns_supported_objects():
    response = client.get("/api/bootstrap")

    assert response.status_code == 200
    payload = response.json()
    assert payload["brand_name"] == "D5 Command Agent"
    assert any(item["key"] == "lead" for item in payload["supported_objects"])


def test_command_endpoint_returns_workspace_url_for_known_command():
    response = client.post("/api/command", json={"command": "all opportunities"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "success"
    assert payload["workspace_url"] == "/opportunities"


def test_command_endpoint_returns_help_examples_for_unknown_command():
    response = client.post("/api/command", json={"command": "please do magic"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "error"
    assert payload["action"] == "help"
    assert len(payload["examples"]) >= 1
