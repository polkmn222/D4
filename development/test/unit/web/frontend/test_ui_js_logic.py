import os

BASE_HTML_PATH = "development/web/frontend/templates/base.html"
LIST_VIEWS_JS_PATH = "development/web/frontend/static/js/list_views.js"
BULK_ACTION_JS_PATH = "development/web/frontend/static/js/bulk_action.js"
TRASH_TEMPLATE_PATH = "development/web/frontend/templates/trash/list_view.html"
FORM_MODAL_TEMPLATE_PATH = "development/web/frontend/templates/templates/sf_form_modal.html"
FORM_ROUTER_PATH = "development/web/backend/app/api/form_router.py"
SEND_MESSAGE_TEMPLATE_PATH = "development/web/message/frontend/templates/send_message.html"

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

    def test_base_html_search_preserves_input_focus_and_ignores_stale_responses(self):
        html = _read(BASE_HTML_PATH)
        assert "function preserveSearchInputSelection(input, callback) {" in html
        assert "let searchRequestSequence = 0;" in html
        assert "const activeRequestSequence = ++searchRequestSequence;" in html
        assert "if (activeRequestSequence !== searchRequestSequence) {" in html
        assert "preserveSearchInputSelection(searchInput, () => renderSearchDropdown(suggestions, false));" in html

    def test_base_html_uses_timeout_guard_for_modal_and_json_loading(self):
        html = _read(BASE_HTML_PATH)
        assert "const GLOBAL_LOADING_FETCH_TIMEOUT_MS = 12000;" in html
        assert "function fetchWithTimeout(resource, options = {}, timeoutMs = GLOBAL_LOADING_FETCH_TIMEOUT_MS) {" in html
        assert "fetchWithTimeout(url)" in html
        assert "return fetchWithTimeout(url, {" in html
        assert "function showConfirmModal(title, msg, onConfirm, confirmLabel = 'Delete') {" in html

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

    def test_list_views_js_persists_recent_records_and_saved_views(self):
        js = _read(LIST_VIEWS_JS_PATH)
        assert "function readRecentListViewRecords" in js
        assert "function rememberRecentlyViewedRecord" in js
        assert "localStorage.setItem(storageKey, JSON.stringify(records.slice(0, 20)))" in js
        assert "requestLeadListView(url, method, payload)" in js

    def test_bulk_action_js_updates_button_and_calls_shared_endpoint(self):
        js = _read(BULK_ACTION_JS_PATH)
        assert "function toggleAllCheckboxes(source)" in js
        assert "updateDeleteButtonState();" in js
        assert "Delete (${checkboxes.length})" in js
        assert "fetch('/bulk/delete'" in js
        assert "showConfirmModal(title, message, () => {" in js

    def test_trash_template_has_search_windowing_and_load_more_logic(self):
        html = _read(TRASH_TEMPLATE_PATH)
        assert "const trashState = {" in html
        assert "function handleTrashSearch(query)" in html
        assert "function applyTrashFiltersAndWindowing()" in html
        assert "Loading more deleted records..." in html
        assert "document.addEventListener('DOMContentLoaded', () => {" in html

    def test_opportunity_form_router_hides_status_and_keeps_contact_field(self):
        source = _read(FORM_ROUTER_PATH)
        assert 'fields = ["contact", "name", "amount", "stage", "brand", "model", "product", "asset", "probability"]' in source

    def test_form_modal_keeps_lookup_hidden_inputs_for_edit_submissions(self):
        html = _read(FORM_MODAL_TEMPLATE_PATH)
        assert '<input type="hidden" name="${fieldName}" id="lookup-id-${fieldName}" value="${initialValueId || \'\'}">' in _read("development/web/frontend/static/js/lookup.js")

    def test_send_message_searches_preserve_focus_and_selection(self):
        html = _read(SEND_MESSAGE_TEMPLATE_PATH)
        assert "function preserveInputFocusAndSelection(input, callback) {" in html
        assert "preserveInputFocusAndSelection(searchInput, () => {" in html
        assert "const query = (searchInput?.value || '').toLowerCase();" in html
        assert "renderTemplateSearchResults(term, selectedValue);" in html

    def test_form_modal_template_image_uses_staged_clear_state(self):
        html = _read(FORM_MODAL_TEMPLATE_PATH)
        assert '<input type="hidden" id="modal-form-remove-image" name="remove_image" value="false">' in html
        assert 'function openModalTemplateImagePicker(trigger) {' in html
        assert "onclick=\"openModalTemplateImagePicker(this)\"" in html
        assert "style=\"color: var(--error);\" onclick=\"clearModalTemplateImageSelection(this)\"" in html
        assert "removeInput.value = imageInput.dataset.currentUrl ? 'true' : 'false';" in html
        assert "const hasPendingRemoval = removeImageInput?.value === 'true';" in html
