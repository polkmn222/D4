# Phase 189 Task

## Objective

Stabilize AI Agent lead CRUD so lead create, update, and delete work reliably through the chat experience, update PostgreSQL immediately through the shared web services, and return output that matches the active AI Agent table schema contract.

## Requested Scope

1. Normalize AI Agent lead CRUD behavior against the shared web lead logic.
2. Remove the extra delete-confirmation roundtrip after the user already confirms from the chat UI.
3. Enforce lead table output with:
   - `display_name = first_name + last_name`
   - model name output instead of raw model ID
   - field ordering and naming aligned with the active frontend schema
4. Keep the work focused on leads first so the same pattern can be extended to other objects later.

## Constraints

- Do not perform manual testing.
- Add unit coverage for the changed lead CRUD and schema behavior.
- Keep historical phase artifacts immutable.
- Back up only the modified modules and files under `backups/101_199/phase189/` before editing.

## Success Criteria

- Lead create/update/delete from AI Agent use the shared service layer and commit to the database.
- AI Agent returns clear success or failure messages for lead CRUD actions.
- A single user confirmation from the AI Agent UI is enough to delete a lead.
- Lead query output matches the frontend schema contract with stable field names and values.
- Targeted lead-focused unit tests pass.
