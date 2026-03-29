from pathlib import Path


BASE_TEMPLATE = (
    Path(__file__).resolve().parents[4]
    / "web"
    / "frontend"
    / "templates"
    / "base.html"
)


def test_global_loading_skips_ai_agent_window_events():
    source = BASE_TEMPLATE.read_text(encoding="utf-8")

    assert "function shouldSkipGlobalLoading(element) {" in source
    assert "element.closest('#ai-agent-window')" in source
