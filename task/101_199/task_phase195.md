## Phase 195 Task

### Goal

Fix two remaining UI contract gaps:

- MessageTemplate detail must only show the `Image` field when the record type is `MMS`
- AI Agent lead flows must use a stable lead-first `OPEN_RECORD` contract after create, update, and manage

### Scope

- Restore MessageTemplate detail visibility after inline type edits are cancelled
- Refactor lead handling in AI Agent so `MANAGE`, `CREATE`, and `UPDATE` all return the same `OPEN_RECORD` shape
- Add focused regression coverage for the lead-first contract and template detail visibility resync

### Constraint

- No manual testing
- Keep the rewrite focused on leads first, then expand to other objects later
