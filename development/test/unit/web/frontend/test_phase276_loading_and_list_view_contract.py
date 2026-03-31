from pathlib import Path


BASE_TEMPLATE = Path("development/web/frontend/templates/base.html")
SEND_MESSAGE_TEMPLATE = Path("development/web/message/frontend/templates/send_message.html")
LIST_VIEWS_JS = Path("development/web/frontend/static/js/list_views.js")
LIST_VIEWS_CSS = Path("development/web/frontend/static/css/list_views.css")
MESSAGING_JS = Path("development/web/frontend/static/js/messaging.js")
AI_AGENT_SERVICE = Path("development/ai_agent/ui/backend/service.py")


def test_global_loading_is_delayed_and_no_longer_force_hides_after_button_click():
    source = BASE_TEMPLATE.read_text(encoding="utf-8")

    assert "let globalLoadingTimer = null;" in source
    assert "const GLOBAL_LOADING_DELAY_MS = 1000;" in source
    assert "const GLOBAL_LOADING_FETCH_TIMEOUT_MS = 12000;" in source
    assert "globalLoadingTimer = setTimeout(() => {" in source
    assert "}, GLOBAL_LOADING_DELAY_MS);" in source
    assert "function fetchWithTimeout(resource, options = {}, timeoutMs = GLOBAL_LOADING_FETCH_TIMEOUT_MS) {" in source
    assert "function shouldTrackNavigationLink(link) {" in source
    assert "fetchWithTimeout(url)" in source
    assert "return fetchWithTimeout(url, {" in source
    assert "function showConfirmModal(title, msg, onConfirm, confirmLabel = 'Delete') {" in source
    assert "deleteBtn.innerText = confirmLabel;" in source
    assert "if (button.closest('#sf-confirm-modal')) {" in source
    assert "return;" in source
    assert "setTimeout(() => hideGlobalLoading(), 1200);" not in source
    assert "if (button.type === 'submit' || button.closest('#sf-confirm-modal')) {" not in source


def test_stt_contract_normalizes_browser_codec_suffixes_before_validation():
    source = AI_AGENT_SERVICE.read_text(encoding="utf-8")

    assert 'raw_content_type = (content_type or "application/octet-stream").lower()' in source
    assert 'safe_type = raw_content_type.split(";", 1)[0].strip()' in source
    assert 'if safe_type not in cls.STT_ALLOWED_CONTENT_TYPES:' in source


def test_send_message_ai_recommend_mode_skips_global_loading_and_selects_visible_rows():
    source = SEND_MESSAGE_TEMPLATE.read_text(encoding="utf-8")

    assert 'id="ai-recommend-mode-modal" class="modal" data-no-loading="true"' in source
    assert 'class="btn ai-recommend-mode-choice" data-no-loading="true"' in source
    assert 'id="select-all" onclick="toggleSelectAll(this)"' in source
    assert "function getVisibleRecipientCheckboxes() {" in source
    assert "function syncRecipientSelectAllState() {" in source
    assert "window.__messagingRecipientApi = {" in source
    assert 'data-selection-key="{{ opp.id }}"' in source
    assert ".filter(row => row.style.display !== 'none' && row.hidden !== true)" in source
    assert "syncRecipientSelectAllState();" in source
    assert "record_type: msg.type," in source
    assert "subject: msg.subject || null," in source
    assert "attachment_id: msg.attachmentId" in source


def test_shared_messaging_module_select_all_tracks_visible_rows_without_style_attribute_match():
    source = MESSAGING_JS.read_text(encoding="utf-8")

    assert "getVisibleCheckboxes()" in source
    assert "syncSelectAllState()" in source
    assert "window.__messagingRecipientApi?.toggleSelectAll" in source
    assert "window.__messagingRecipientApi?.syncSelectAllState" in source
    assert 'data-selection-key="${item.id}"' in source
    assert ".filter((row) => row.style.display !== 'none' && row.hidden !== true)" in source
    assert 'onclick="updateSelectionOrder(this)"' in source
    assert "if (typeof updateSelectionOrder === 'function') {" in source
    assert '.recipient-row[style=""] input[name="selected_recipients"]' not in source


def test_send_message_compose_builds_lms_mms_config_from_current_form_state():
    source = SEND_MESSAGE_TEMPLATE.read_text(encoding="utf-8")

    assert "function buildCurrentMessageConfig() {" in source
    assert "const normalizedType = normalizeComposeType(rawType, content, false);" in source
    assert "subject: normalizedType === 'SMS' ? '' : document.getElementById('message-subject').value," in source
    assert "attachmentId: document.getElementById('message-attachment-id').value," in source


def test_send_message_compose_blocks_mms_without_attachment_and_allows_lms_without_it():
    source = SEND_MESSAGE_TEMPLATE.read_text(encoding="utf-8")

    assert "function validateMessageRules(type, content, subject, attachmentId) {" in source
    assert "if ((type === 'LMS' || type === 'MMS') && bytes > 2000) {" in source
    assert "if (type === 'MMS' && !attachmentId) {" in source
    assert "showToast('MMS messages require a JPG image under 500KB.', true);" in source


def test_list_view_setup_uses_single_save_button_and_hides_delete_for_builtins():
    source = LIST_VIEWS_JS.read_text(encoding="utf-8")

    assert 'const saveNewButton = setupDropdown' in source
    assert 'function closeSetupDropdown() {' in source
    assert 'saveNewButton.style.display = "none";' in source
    assert 'saveViewButton.textContent = activeView.editable ? "Save Changes" : "Save as New";' in source
    assert 'deleteViewButton.style.display = activeView.editable ? "" : "none";' in source
    assert 'window[saveNewViewFunctionName]();' in source
    assert 'closeSetupDropdown();' in source


def test_list_view_setup_defaults_to_empty_filters_and_visible_shell_overflow():
    js_source = LIST_VIEWS_JS.read_text(encoding="utf-8")
    css_source = LIST_VIEWS_CSS.read_text(encoding="utf-8")

    assert "const normalizedConditions = conditions.length ? conditions : [];" in js_source
    assert "activeFilters.push({ ...defaultFilterCondition });" in js_source
    assert 'defaultFilterCondition: { field: "status", operator: "equals", value: "New" }' not in js_source
    assert 'defaultFilterCondition: { field: "stage", operator: "contains", value: "Prospecting" }' not in js_source
    assert 'defaultFilterCondition: { field: "type", operator: "contains", value: "SMS" }' not in js_source
    assert "overflow: visible !important;" in css_source
