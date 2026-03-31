## Phase 336 Implementation

- Updated `development/web/backend/app/services/record_delete_service.py` so message template deletion clears `attachment_id`, `image_url`, and `file_path`, then flushes the change before deleting linked `Attachment` rows.
- Added unit coverage in `development/test/unit/web/backend/app/services/test_record_delete_service.py` for:
  - template delete with a direct `attachment_id`
  - template delete with child attachments by `parent_id`
  - image-only cleanup without attachment rows
