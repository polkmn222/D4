from ai_agent.ui.backend.crud.lead import (
    build_lead_edit_form_response,
    build_lead_open_record_response,
)
from pathlib import Path


class MockLead:
    def __init__(self, record_id="LEAD_MOD_196", first_name="Ada", last_name="Kim"):
        self.id = record_id
        self.first_name = first_name
        self.last_name = last_name


def test_build_lead_edit_form_response_returns_open_form_contract():
    response = build_lead_edit_form_response("LEAD-1", "Ada Kim", "eng")

    assert response["intent"] == "OPEN_FORM"
    assert response["record_id"] == "LEAD-1"
    assert response["form_url"] == "/leads/new-modal?id=LEAD-1"


def test_build_lead_open_record_response_returns_lead_contract():
    lead = MockLead()
    response = build_lead_open_record_response(
        db=None,
        lead=lead,
        conversation_id=None,
        action="manage",
        language_preference="eng",
        build_chat_card=lambda db, lead, mode: {"type": "lead_paste", "mode": mode, "record_id": lead.id},
        lead_name_getter=lambda lead: f"{lead.first_name} {lead.last_name}",
    )

    assert response["intent"] == "OPEN_RECORD"
    assert response["object_type"] == "lead"
    assert response["record_id"] == "LEAD_MOD_196"
    assert response["redirect_url"] == "/leads/LEAD_MOD_196"
    assert response["chat_card"]["mode"] == "view"


def test_ai_agent_extracts_full_form_for_new_modal_workspace():
    source = Path("development/ai_agent/ui/frontend/static/js/ai_agent.js").read_text(encoding="utf-8")

    assert "const form = doc.querySelector('form');" in source
    assert "wrapper.appendChild(form.cloneNode(true));" in source


def test_ai_agent_non_redirect_save_message_points_user_back_to_form():
    source = Path("development/ai_agent/ui/frontend/static/js/ai_agent.js").read_text(encoding="utf-8")

    assert "Save did not complete. Review the highlighted form and try again." in source


def test_ai_agent_workspace_new_modal_uses_embedded_frame_runtime():
    source = Path("development/ai_agent/ui/frontend/static/js/ai_agent.js").read_text(encoding="utf-8")

    assert "function renderAgentWorkspaceFrame(content, url, title) {" in source
    assert 'class="agent-workspace-frame"' in source
    assert "if (url.includes('/new-modal')) {" in source
    assert "renderAgentWorkspaceFrame(content, url, title || 'Form');" in source
    assert "recordAiAgentDebug('workspace-frame-open'" in source


def test_ai_agent_open_record_workspace_title_does_not_fallback_to_record_id():
    source = Path("development/ai_agent/ui/frontend/static/js/ai_agent.js").read_text(encoding="utf-8")

    assert "const workspaceTitle = data.chat_card?.title || data.form_title || 'Record View';" in source
    assert "openAgentWorkspace(targetUrl, workspaceTitle);" in source


def test_ai_agent_lead_table_uses_display_name_before_fallback_fields():
    source = Path("development/ai_agent/ui/frontend/static/js/ai_agent.js").read_text(encoding="utf-8")

    assert "return row.display_name || [row.first_name, row.last_name].filter(Boolean).join(' ').trim() || row.name || '-';" in source


def test_ai_agent_open_form_uses_inline_form_message_for_form_urls():
    source = Path("development/ai_agent/ui/frontend/static/js/ai_agent.js").read_text(encoding="utf-8")

    assert "if (data.intent === 'OPEN_FORM' && data.form_url) {" in source
    assert "appendAgentInlineFormMessage(data.text || 'I opened the form for you.', data.form_url, data.form_title || 'Form');" in source


def test_ai_agent_default_body_keeps_workspace_markup_after_reset():
    source = Path("development/ai_agent/ui/frontend/static/js/ai_agent.js").read_text(encoding="utf-8")

    assert 'const AI_AGENT_DEFAULT_BODY_HTML = `' in source
    assert '<div id="ai-agent-workspace" class="agent-workspace agent-hidden">' in source
    assert '<strong id="ai-agent-workspace-title">Record View</strong>' in source


def test_ai_agent_workspace_repositions_after_latest_message_on_open():
    source = Path("development/ai_agent/ui/frontend/static/js/ai_agent.js").read_text(encoding="utf-8")

    assert "function placeAgentWorkspaceProminently(panel, body) {" in source
    assert "selectionBar.insertAdjacentElement('afterend', panel);" in source
    assert "body.prepend(panel);" in source
    assert "function scrollAgentWorkspaceIntoView(panel, body) {" in source
    assert "body.scrollTo({ top: nextScrollTop, behavior: 'smooth' });" in source


def test_ai_agent_append_chat_message_does_not_force_scroll():
    source = Path("development/ai_agent/ui/frontend/static/js/ai_agent.js").read_text(encoding="utf-8")
    append_start = source.index("function appendChatMessage(")
    append_end = source.index("function removeExistingAgentInlineForms()", append_start)
    append_source = source[append_start:append_end]

    assert "function appendChatMessage(" in append_source
    assert "scrollIntoView({ behavior: 'smooth'" not in append_source


def test_ai_agent_debug_panel_markup_exists_in_template():
    source = Path("development/ai_agent/ui/frontend/templates/ai_agent_panel.html").read_text(encoding="utf-8")

    assert 'id="ai-agent-debug-toggle"' in source
    assert 'onclick="toggleAiAgentDebug()"' in source
    assert 'id="ai-agent-debug-panel"' in source
    assert 'id="ai-agent-debug-log"' in source


def test_ai_agent_debug_runtime_logging_exists_for_workspace_flow():
    source = Path("development/ai_agent/ui/frontend/static/js/ai_agent.js").read_text(encoding="utf-8")

    assert "let aiAgentDebugEnabled = localStorage.getItem('aiAgentDebugEnabled');" in source
    assert "aiAgentDebugEnabled = aiAgentDebugEnabled === '1';" in source
    assert "function recordAiAgentDebug(stage, details = {})" in source
    assert "recordAiAgentDebug('intent-open-form'" in source
    assert "recordAiAgentDebug('workspace-frame-open'" in source
    assert "recordAiAgentDebug('workspace-frame-load'" in source
    assert "recordAiAgentDebug('form-response'" in source


def test_ai_agent_debug_panel_styles_exist():
    source = Path("development/ai_agent/ui/frontend/static/css/ai_agent.css").read_text(encoding="utf-8")

    assert ".ai-agent-debug-panel" in source
    assert ".ai-agent-debug-log" in source
    assert ".agent-debug-toggle.is-active" in source


def test_ai_agent_workspace_frame_style_exists():
    source = Path("development/ai_agent/ui/frontend/static/css/ai_agent.css").read_text(encoding="utf-8")

    assert ".agent-workspace-frame" in source
    assert "min-height: 720px;" in source
