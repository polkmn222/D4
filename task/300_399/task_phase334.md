# Phase 334 Task Record

## Scope

- Fix AI Agent `message_template` create/edit inline form field visibility so `subject` and `image` follow the selected type (`SMS`, `LMS`, `MMS`) consistently.

## Constraints

- Stay within the single requested issue only.
- Keep the existing web modal UI and routing.
- Do not broaden into unrelated grouped-object edit work.
- Unit tests are mandatory.
- Manual testing is forbidden.
- SQLite is forbidden.

## Success Criteria

- AI Agent inline `message_template` forms apply the correct field visibility on initial render.
- Changing type inside the inline form continues to update `subject` and `image` visibility.
- Focused frontend DOM unit tests pass.
