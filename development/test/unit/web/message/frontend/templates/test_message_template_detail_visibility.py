from pathlib import Path


def test_message_template_detail_resyncs_image_visibility_after_cancel():
    source = Path("development/web/message/frontend/templates/message_templates/detail_view.html").read_text(encoding="utf-8")

    assert "function syncTemplateDetailFieldVisibility" in source
    assert "window.cancelBatchEdit = function (...args)" in source
    assert "syncTemplateDetailFieldVisibility();" in source
