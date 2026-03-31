## Phase 329 Implementation

- Updated [development/web/message/frontend/templates/send_message.html](/Users/sangyeol.park@gruve.ai/Documents/D5/development/web/message/frontend/templates/send_message.html) to remove the separate Saved Recipients summary card.
- Moved the collapsible staged recipients table so it renders directly below the recipients table instead of inside the right-side action column.
- Updated [development/test/unit/web/message/backend/test_message_template_modal_submission.py](/Users/sangyeol.park@gruve.ai/Documents/D5/development/test/unit/web/message/backend/test_message_template_modal_submission.py) to match the revised staged recipients layout.

## Backups

- Backed up only changed module folders under [backups/300_399/phase329](/Users/sangyeol.park@gruve.ai/Documents/D5/backups/300_399/phase329):
  - `development/web/message`
  - `development/test/unit`
