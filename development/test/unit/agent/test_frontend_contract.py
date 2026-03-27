from pathlib import Path


def test_dashboard_template_keeps_agent_button_and_assets():
    source = Path("development/web/frontend/templates/dashboard/dashboard.html").read_text(encoding="utf-8")

    assert '<link rel="stylesheet" href="/agent/static/css/app.css">' in source
    assert '<script src="/agent/static/js/app.js" defer></script>' in source
    assert 'onclick="toggleOpsPilot()"' in source
    assert 'Open Ops Pilot' in source
    assert 'id="ops-pilot-root"' in source


def test_agent_panel_contains_command_workspace_shell():
    source = Path("development/agent/ui/frontend/templates/agent_panel.html").read_text(encoding="utf-8")

    assert 'id="ops-pilot-command"' in source
    assert 'id="ops-pilot-object-buttons"' in source
    assert 'id="ops-pilot-prompt-list"' in source
    assert 'id="ops-pilot-transcript"' in source
    assert 'id="ops-pilot-frame"' in source
    assert 'D5 Command Agent' in source


def test_agent_frontend_bootstraps_panel_and_routes_commands_to_workspace():
    source = Path("development/agent/ui/frontend/static/js/app.js").read_text(encoding="utf-8")

    assert "fetch('/agent-panel')" in source
    assert "fetch('/agent/api/bootstrap')" in source
    assert "fetch('/agent/api/command'" in source
    assert "frame.src = payload.workspace_url;" in source
    assert "appendOpsPilotCard('user', command);" in source
    assert "appendOpsPilotCard('assistant', payload.message, payload.examples || []);" in source
    assert "window.toggleOpsPilot = toggleOpsPilot;" in source


def test_agent_frontend_styles_define_shell_transcript_and_workspace():
    source = Path("development/agent/ui/frontend/static/css/app.css").read_text(encoding="utf-8")

    assert ".ops-pilot-window" in source
    assert ".ops-pilot-layout" in source
    assert ".ops-pilot-sidebar" in source
    assert ".ops-pilot-transcript" in source
    assert ".ops-pilot-workspace" in source
    assert ".ops-pilot-frame" in source
    assert ".agent-paste-card" in source

