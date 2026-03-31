from pathlib import Path


def test_ai_agent_quick_guide_template_adds_recent_and_pinned_section():
    source = Path("development/ai_agent/ui/frontend/templates/ai_agent_panel.html").read_text(encoding="utf-8")

    assert 'data-ai-guide-section-history' in source
    assert 'id="ai-agent-activity-list"' in source
    assert 'id="ai-agent-activity-empty"' in source


def test_ai_agent_quick_guide_js_tracks_recent_commands_and_pin_state():
    source = Path("development/ai_agent/ui/frontend/static/js/ai_agent.js").read_text(encoding="utf-8")

    assert "const AI_AGENT_QUICK_GUIDE_STORAGE_KEY = 'aiAgentQuickGuideActivity';" in source
    assert "function recordQuickGuideActivity(query, label = null) {" in source
    assert "function toggleQuickGuidePin(id) {" in source
    assert "function renderQuickGuideActivityList() {" in source
    assert "renderQuickGuideActivityList();" in source


def test_ai_agent_send_recipients_requires_selection_and_template_or_content():
    source = Path("development/ai_agent/ui/frontend/static/js/ai_agent.js").read_text(encoding="utf-8")

    assert "const canSaveRecipients = selectedCount > 0 && hasMessageBody;" in source
    assert "Choose a template or enter message content before saving recipients." in source
    assert "Save Recipients" in source
