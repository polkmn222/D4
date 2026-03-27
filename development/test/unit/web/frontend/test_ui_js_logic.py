import os

BASE_HTML_PATH = "development/web/frontend/templates/base.html"
LIST_VIEWS_JS_PATH = "development/web/frontend/static/js/list_views.js"

def _read(path: str) -> str:
    with open(path, "r") as f:
        return f.read()

class TestUIJSLogic:
    def test_base_html_search_categorization_exists(self):
        html = _read(BASE_HTML_PATH)
        assert 'const categories = {};' in html
        assert 'categories[item.type].push(item);' in html
        assert 'renderSearchItem(item, itemIdx++, false);' in html

    def test_base_html_search_keyboard_nav_exists(self):
        html = _read(BASE_HTML_PATH)
        assert "e.key === 'ArrowDown'" in html
        assert "searchSelectedIndex = Math.min" in html
        assert "items[searchSelectedIndex].click()" in html

    def test_list_views_js_skeleton_init_exists(self):
        js = _read(LIST_VIEWS_JS_PATH)
        assert 'document.getElementById("gk-list-skeleton")' in js
        assert 'table.closest(".sf-table-wrapper")' in js

    def test_list_views_js_skeleton_visibility_logic_exists(self):
        js = _read(LIST_VIEWS_JS_PATH)
        # Should hide skeleton in updateEmptyState
        assert 'if (listSkeleton) listSkeleton.style.display = "none"' in js
        # Should show skeleton in renderView
        assert 'listSkeleton.style.display = "block"' in js
        # Should hide tableWrapper when loading
        assert 'tableWrapper.style.display = "none"' in js

    def test_list_views_js_render_view_has_delay(self):
        js = _read(LIST_VIEWS_JS_PATH)
        # Verify the 150ms delay for skeleton loader
        assert 'setTimeout(() => {' in js
        assert '}, 150)' in js
