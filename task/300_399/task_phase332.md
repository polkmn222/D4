# Phase 332 Task Record

## Scope

- Redesign AI Agent `brand`, `model`, `asset`, and `message_template` edit saves so they follow the same AI-managed in-chat save continuity pattern as the rolled-out chat flows while keeping the existing web form UI.

## Constraints

- Stay within the single requested issue only.
- Keep the existing web form UI and validation rules.
- Do not broaden to unrelated AI Agent interactions.
- Unit tests are mandatory.
- Manual testing is forbidden.
- SQLite is forbidden.

## Success Criteria

- AI Agent inline edit forms for `brand`, `model`, `asset`, and `message_template` are recognized by the AI-managed submit bridge.
- Successful saves return refreshed `OPEN_RECORD` continuity in chat.
- `message_template` forms keep the web modal UI path and bypass AI-managed submit when a new file is selected.
- Focused backend and frontend unit tests pass.
