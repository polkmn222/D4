import os


BASE_DIR = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..")
)
JS_PATH = os.path.join(BASE_DIR, "ai_agent", "ui", "frontend", "static", "js", "ai_agent.js")
CSS_PATH = os.path.join(BASE_DIR, "ai_agent", "ui", "frontend", "static", "css", "ai_agent.css")
TEMPLATE_PATH = os.path.join(BASE_DIR, "ai_agent", "ui", "frontend", "templates", "ai_agent_panel.html")


def _read(path: str) -> str:
    with open(os.path.normpath(path), "r", encoding="utf-8") as handle:
        return handle.read()


class TestWorkspacePlacementContract:
    def test_workspace_is_promoted_near_top_of_agent_body(self):
        js = _read(JS_PATH)

        assert "function placeAgentWorkspaceProminently(panel, body) {" in js
        assert "selectionBar.insertAdjacentElement('afterend', panel);" in js
        assert "body.prepend(panel);" in js

    def test_workspace_scroll_helper_targets_agent_body(self):
        js = _read(JS_PATH)

        assert "function scrollAgentWorkspaceIntoView(panel, body) {" in js
        assert "const nextScrollTop = Math.max(panelTop - bodyTop - 8, 0);" in js
        assert "body.scrollTo({ top: nextScrollTop, behavior: 'smooth' });" in js

    def test_workspace_open_paths_use_prominent_placement_and_scroll(self):
        js = _read(JS_PATH)

        assert "placeAgentWorkspaceProminently(panel, body);" in js
        assert "scrollAgentWorkspaceIntoView(panel, body);" in js

    def test_new_modal_paths_use_embedded_frame(self):
        js = _read(JS_PATH)

        assert "function renderAgentWorkspaceFrame(content, url, title) {" in js
        assert 'class="agent-workspace-frame"' in js
        assert "recordAiAgentDebug('workspace-frame-open'" in js


class TestDebugDefaultContract:
    def test_debug_defaults_to_off_without_local_storage_opt_in(self):
        js = _read(JS_PATH)

        assert "let aiAgentDebugEnabled = localStorage.getItem('aiAgentDebugEnabled');" in js
        assert "aiAgentDebugEnabled = aiAgentDebugEnabled === '1';" in js

    def test_debug_toggle_markup_still_exists(self):
        template = _read(TEMPLATE_PATH)

        assert 'id="ai-agent-debug-toggle"' in template
        assert 'onclick="toggleAiAgentDebug()"' in template


class TestWorkspaceVisualSupport:
    def test_workspace_css_still_defines_standalone_panel_container(self):
        css = _read(CSS_PATH)

        assert ".agent-workspace {" in css
        assert ".agent-workspace-frame {" in css
        assert ".agent-workspace-header {" in css
        assert ".agent-workspace-content {" in css

    def test_debug_panel_css_remains_optional(self):
        css = _read(CSS_PATH)

        assert ".ai-agent-debug-panel.agent-hidden" in css
        assert "display: none !important;" in css
