from pathlib import Path

from agent.ui.backend.service import (
    build_agent_bootstrap_payload,
    parse_agent_command,
    resolve_object,
)


def test_bootstrap_payload_exposes_multi_object_workspace():
    payload = build_agent_bootstrap_payload()

    assert payload["brand_name"] == "D5 Command Agent"
    assert payload["default_command"] == "all leads"
    assert len(payload["supported_objects"]) == 7


def test_object_resolution_accepts_plural_and_alias_forms():
    assert resolve_object("leads")["key"] == "lead"
    assert resolve_object("opps")["key"] == "opportunity"
    assert resolve_object("vehicle specifications")["key"] == "brand"


def test_parse_command_supports_list_create_open_and_edit():
    assert parse_agent_command("all leads")["workspace_url"] == "/leads"
    assert parse_agent_command("new contact")["workspace_url"] == "/contacts/new-modal"
    assert parse_agent_command("open product 01TABC123")["workspace_url"] == "/products/01TABC123"
    assert parse_agent_command("edit model a0MABC123")["workspace_url"] == "/models/new-modal?id=a0MABC123"


def test_parse_command_returns_help_payload_for_unknown_input():
    payload = parse_agent_command("do something impossible")

    assert payload["status"] == "error"
    assert payload["action"] == "help"
    assert "supported patterns" in payload["message"]


def test_main_app_mounts_standalone_agent_subapp():
    source = Path("development/web/backend/app/main.py").read_text(encoding="utf-8")

    assert 'from agent.ui.backend.main import app as ops_agent_app' in source
    assert 'app.mount("/agent", ops_agent_app)' in source


def test_dashboard_router_exposes_agent_panel_fragment():
    source = Path("development/web/backend/app/api/routers/dashboard_router.py").read_text(encoding="utf-8")

    assert '@router.get("/agent-panel", response_class=HTMLResponse)' in source
    assert 'return templates.TemplateResponse(request, "agent_panel.html", {"request": request})' in source

