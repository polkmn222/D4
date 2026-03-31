from types import SimpleNamespace
from unittest.mock import MagicMock, call, patch

from web.backend.app.services.record_delete_service import RecordDeleteService


def test_delete_template_attachments_clears_template_reference_before_attachment_delete():
    template = SimpleNamespace(
        id="TPL_336",
        attachment_id="ATT_MAIN",
        image_url="/static/uploads/message_templates/main.jpg",
        file_path="/static/uploads/message_templates/main.jpg",
    )
    linked_attachment = SimpleNamespace(id="ATT_MAIN", file_path="/static/uploads/message_templates/main.jpg", provider_key="prov-main")
    child_attachment = SimpleNamespace(id="ATT_CHILD", file_path="/static/uploads/message_templates/child.jpg", provider_key="prov-child")

    parent_attachment_query = MagicMock()
    parent_attachment_query.filter.return_value.all.return_value = [child_attachment]

    main_attachment_query = MagicMock()
    main_attachment_query.filter.return_value.first.return_value = linked_attachment

    child_attachment_query = MagicMock()
    child_attachment_query.filter.return_value.first.return_value = child_attachment

    db = MagicMock()
    db.query.side_effect = [parent_attachment_query, main_attachment_query, child_attachment_query]

    with patch("web.backend.app.services.record_delete_service.PublicImageStorageService.delete_image") as delete_image:
        RecordDeleteService._delete_template_attachments(db, template)

    assert template.attachment_id is None
    assert template.image_url == ""
    assert template.file_path == ""
    assert db.flush.call_count == 1
    assert db.delete.call_args_list == [call(linked_attachment), call(child_attachment)]
    flush_index = next(index for index, entry in enumerate(db.mock_calls) if entry == call.flush())
    delete_index = next(index for index, entry in enumerate(db.mock_calls) if entry == call.delete(linked_attachment))
    assert flush_index < delete_index
    assert delete_image.call_args_list == [
        call(file_path=linked_attachment.file_path, provider_key=linked_attachment.provider_key),
        call(file_path=child_attachment.file_path, provider_key=child_attachment.provider_key),
    ]


def test_delete_template_attachments_without_attachment_deletes_public_image_only():
    template = SimpleNamespace(
        id="TPL_336_NO_ATTACHMENT",
        attachment_id=None,
        image_url="/static/uploads/message_templates/orphan.jpg",
        file_path="/static/uploads/message_templates/orphan.jpg",
    )

    parent_attachment_query = MagicMock()
    parent_attachment_query.filter.return_value.all.return_value = []

    db = MagicMock()
    db.query.return_value = parent_attachment_query

    with patch("web.backend.app.services.record_delete_service.PublicImageStorageService.delete_image") as delete_image:
        RecordDeleteService._delete_template_attachments(db, template)

    db.flush.assert_not_called()
    db.delete.assert_not_called()
    delete_image.assert_called_once_with(template.image_url)
