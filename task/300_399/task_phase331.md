# Phase 331 Task Record

## Scope

- Fix the AI Agent maximize action so it does not jump the chat body scroll position to the top.

## Constraints

- Stay within the single requested issue only.
- Unit tests are mandatory.
- Manual testing is forbidden.
- SQLite is forbidden.

## Success Criteria

- Toggling AI Agent maximize preserves the current `#ai-agent-body` scroll position.
- The maximize state still applies normally.
- Focused AI Agent frontend DOM unit tests pass.
