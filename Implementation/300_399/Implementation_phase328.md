## Phase 328 Implementation

- Updated [development/web/message/frontend/templates/send_message.html](/Users/sangyeol.park@gruve.ai/Documents/D5/development/web/message/frontend/templates/send_message.html) so:
  - template selection uses a lookup-style searchable input with a filtered result list
  - the underlying template `<select>` remains as hidden state for existing apply/save behavior
  - saved recipients render into a collapsible staged table for easier review
- Updated [development/ai_agent/ui/frontend/static/js/ai_agent.js](/Users/sangyeol.park@gruve.ai/Documents/D5/development/ai_agent/ui/frontend/static/js/ai_agent.js) so:
  - local results-table search filters against visible schema fields instead of hidden row JSON
  - `/new-modal` workspace extraction preserves trailing shared modal scripts, which restores template type-based field visibility and shared inline modal behavior in AI Agent
- Added and updated unit coverage in:
  - [development/test/unit/web/message/backend/test_message_template_modal_submission.py](/Users/sangyeol.park@gruve.ai/Documents/D5/development/test/unit/web/message/backend/test_message_template_modal_submission.py)
  - [development/test/unit/ai_agent/frontend/test_ai_agent_continuity_dom.py](/Users/sangyeol.park@gruve.ai/Documents/D5/development/test/unit/ai_agent/frontend/test_ai_agent_continuity_dom.py)

## Backups

- Backed up only changed module folders under [backups/300_399/phase328](/Users/sangyeol.park@gruve.ai/Documents/D5/backups/300_399/phase328):
  - `development/web/message`
  - `development/ai_agent/ui`
  - `development/test/unit`
