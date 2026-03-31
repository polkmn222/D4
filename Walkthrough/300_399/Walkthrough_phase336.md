## Phase 336 Walkthrough

- Reproduced the failure path in code inspection: `RecordDeleteService._delete_template_attachments()` deleted `Attachment` rows before the `MessageTemplate` foreign key reference was cleared.
- Fixed the ordering inside the shared delete service so both web and AI Agent delete flows use the corrected sequence.

## Verification

- Command:
  - `PYTHONPATH=development pytest -m unit development/test/unit/web/backend/app/services/test_record_delete_service.py development/test/unit/web/message/backend/test_message_template_image_routes.py -q`
- Result:
  - `5 passed`
