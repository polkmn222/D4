# Phase 197 Task

## Scope

- Make AI Agent chat CRUD flows report save success or failure in chat and, on success, open the saved record tab naturally in the chat workspace.
- Prevent template image selection from becoming a committed backend save before the user presses `Save`.
- Keep the work limited to the AI Agent UI flow and message-template modal flow.

## Constraints

- Do not read historical `Implementation`, `task`, `Walkthrough`, or backup folders.
- Back up only the modules that will be modified under `backups/101_199/phase197/`.
- Manual testing is forbidden.
- Unit tests are required.
- If a suspicious or unrelated issue appears outside this scope, stop and report it instead of changing it.

## Success Criteria

- AI Agent inline save surfaces success or failure text in chat.
- After a successful create or edit from the AI Agent inline form, the saved record opens in the chat workspace.
- Selecting a template image from the edit/create modal does not persist the change until the user presses `Save`.
- Focused unit tests cover the changed behavior and pass.
