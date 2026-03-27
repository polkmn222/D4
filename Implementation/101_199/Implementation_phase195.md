## Phase 195 Implementation

### Lead-First AI Agent Contract

- Added a dedicated lead response builder in [service.py](/Users/sangyeol.park@gruve.ai/Documents/D5/development/ai_agent/ui/backend/service.py) so lead `MANAGE`, `CREATE`, and `UPDATE` now all return:
  - `intent=OPEN_RECORD`
  - `object_type=lead`
  - `record_id`
  - `redirect_url`
  - `chat_card`
  - natural language status text
- Updated the AI Agent frontend in [ai_agent.js](/Users/sangyeol.park@gruve.ai/Documents/D5/development/ai_agent/ui/frontend/static/js/ai_agent.js) to open the workspace from `redirect_url` first and fall back to a detail route derived from `object_type + record_id`.

### MessageTemplate Detail Visibility

- Added a detail-page visibility sync in [detail_view.html](/Users/sangyeol.park@gruve.ai/Documents/D5/development/web/message/frontend/templates/message_templates/detail_view.html).
- The page now re-evaluates `Type` and hides `Image` whenever the template is not `MMS`, including after `cancelBatchEdit()`.

### Regression Coverage

- Added lead contract coverage for `MANAGE -> OPEN_RECORD`.
- Added template detail visibility source coverage to ensure resync remains wired.
