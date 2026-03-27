from io import BytesIO
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from starlette.datastructures import Headers, UploadFile

from web.message.backend.routers.message_template_router import (
    clear_template_image,
    template_upload,
    update_template_route,
)


def _upload_file(name: str, content: bytes, content_type: str) -> UploadFile:
    return UploadFile(file=BytesIO(content), filename=name, headers=Headers({"content-type": content_type}))


@pytest.mark.asyncio
async def test_template_upload_success_updates_attachment_fields():
    db = MagicMock()
    template = SimpleNamespace(id="TPL_1", attachment_id=None, image_url="", file_path="")
    stored_image = SimpleNamespace(file_path="/static/uploads/message_templates/test.jpg", provider_key="cloudinary")
    attachment = SimpleNamespace(id="ATT_1")

    with patch("web.message.backend.routers.message_template_router.MessageTemplateService.get_template", return_value=template), \
         patch("web.message.backend.routers.message_template_router.MessageTemplateService.validate_template_image_upload"), \
         patch("web.message.backend.routers.message_template_router.PublicImageStorageService.upload_message_template_image", return_value=stored_image), \
         patch("web.message.backend.routers.message_template_router.AttachmentService.create_attachment", return_value=attachment):
        result = await template_upload(
            request=MagicMock(),
            template_id="TPL_1",
            file=_upload_file("test.jpg", b"jpg-bytes", "image/jpeg"),
            db=db,
        )

    assert result["status"] == "success"
    assert result["attachment_id"] == "ATT_1"
    assert template.image_url == "/static/uploads/message_templates/test.jpg"
    assert template.attachment_id == "ATT_1"


@pytest.mark.asyncio
async def test_update_template_route_clears_image_when_switching_off_mms():
    db = MagicMock()
    template = SimpleNamespace(id="TPL_2", attachment_id="ATT_OLD", image_url="/static/old.jpg", file_path="/static/old.jpg")

    with patch("web.message.backend.routers.message_template_router.MessageTemplateService.get_template", return_value=template), \
         patch("web.message.backend.routers.message_template_router.MessageTemplateService.update_template"), \
         patch("web.message.backend.routers.message_template_router._remove_template_image") as mock_remove:
        response = await update_template_route(
            request=MagicMock(),
            template_id="TPL_2",
            name="Template",
            subject="Subject",
            content="Body",
            description=None,
            record_type="SMS",
            image=None,
            db=db,
        )

    assert response.status_code == 303
    assert response.headers["location"] == "/message_templates/TPL_2?success=Record+updated+successfully"
    mock_remove.assert_called_once_with(db, template)
    assert template.image_url == ""
    assert template.file_path == ""
    assert template.attachment_id is None


@pytest.mark.asyncio
async def test_clear_template_image_resets_fields():
    db = MagicMock()
    template = SimpleNamespace(id="TPL_3", attachment_id="ATT_OLD", image_url="/static/old.jpg", file_path="/static/old.jpg")

    with patch("web.message.backend.routers.message_template_router.MessageTemplateService.get_template", return_value=template), \
         patch("web.message.backend.routers.message_template_router._remove_template_image") as mock_remove:
        result = await clear_template_image(
            request=MagicMock(),
            template_id="TPL_3",
            db=db,
        )

    assert result["status"] == "success"
    mock_remove.assert_called_once_with(db, template)
    assert template.image_url == ""
    assert template.file_path == ""
    assert template.attachment_id is None
