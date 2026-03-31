from pathlib import Path


MODELS_PATH = Path("development/db/models.py")
DB_PATH = Path("development/db/database.py")


def test_message_send_model_includes_delivery_metadata_fields():
    source = MODELS_PATH.read_text(encoding="utf-8")

    assert "subject = Column(String, nullable=True)" in source
    assert 'record_type = Column(String, default="SMS")' in source
    assert "image_url = Column(String, nullable=True)" in source
    assert 'attachment_id = Column(String(18), ForeignKey("attachments.id"), nullable=True)' in source


def test_runtime_bootstrap_adds_missing_message_send_columns():
    source = DB_PATH.read_text(encoding="utf-8")

    assert 'if table_name == "message_sends":' in source
    assert 'ALTER TABLE message_sends ADD COLUMN subject VARCHAR' in source
    assert 'ALTER TABLE message_sends ADD COLUMN record_type VARCHAR' in source
    assert 'ALTER TABLE message_sends ADD COLUMN image_url VARCHAR' in source
    assert 'ALTER TABLE message_sends ADD COLUMN attachment_id VARCHAR(18)' in source
