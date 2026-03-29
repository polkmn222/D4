from pathlib import Path


def test_ai_agent_frontend_debug_includes_chat_request_and_response_events():
    source = Path("development/ai_agent/ui/frontend/static/js/ai_agent.js").read_text(encoding="utf-8")

    assert "recordAiAgentDebug('chat-request'" in source
    assert "recordAiAgentDebug('chat-response'" in source
    assert "recordAiAgentDebug('chat-handle-intent'" in source


def test_ai_agent_frontend_debug_includes_chat_form_request_and_response_events():
    source = Path("development/ai_agent/ui/frontend/static/js/ai_agent.js").read_text(encoding="utf-8")

    assert "recordAiAgentDebug('chat-form-request'" in source
    assert "recordAiAgentDebug('chat-form-response'" in source
    assert "recordAiAgentDebug('chat-form-open-record'" in source
    assert "recordAiAgentDebug('chat-form-submit-error'" in source
