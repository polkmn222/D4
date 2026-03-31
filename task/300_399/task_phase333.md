# Phase 333 Task Record

## Scope

- Redesign AI Agent grouped-object `Edit` actions so `brand`, `model`, `asset`, and `message_template` open their inline edit forms directly instead of behaving like `Open`.

## Constraints

- Stay within the single requested issue only.
- Do not broaden into search, quick guide, or send-recipient work.
- Keep `Open` and `Edit` behavior separate.
- Unit tests are mandatory.
- Manual testing is forbidden.
- SQLite is forbidden.

## Success Criteria

- Grouped-object chat-card `Edit` buttons open inline edit forms directly.
- Grouped-object selection-bar `Edit` opens inline edit forms directly.
- Workspace-header `Edit` uses the same direct edit-form path for the grouped objects.
- Focused frontend DOM unit tests pass.
