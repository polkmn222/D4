# Phase 199 Task

## Scope

- Fix AI Agent lead create/edit so it reuses the web modal CRUD contract correctly.
- Ensure save from the AI Agent actually submits the underlying form, persists to the database, and opens the saved record in the AI Agent workspace.
- Add focused automated coverage.

## Constraints

- Keep changes limited to the AI Agent inline workspace flow and related tests.
- Use the web lead CRUD flow as the canonical contract.
- Unit tests are required.
- Manual validation is requested for this phase after automated verification.

## Success Criteria

- AI Agent inline create/edit keeps the form wrapper intact.
- Save persists data through the normal web lead routes.
- Successful save reports status in chat and opens the saved record in the workspace.
