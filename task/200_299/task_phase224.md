# Task Phase 224: Investigate and Fix Standalone Agent CRUD UI

## Scope
- Investigate why the UI in the `agent` folder is not working properly for CRUD operations.
- Ensure CRUD (Create, Read, Update, Delete) is fully functional in the standalone agent (Ops Pilot).
- Improve the REST API endpoints in `agent/ui/backend/router.py` to support all necessary Lead fields and partial updates.
- Verify the iframe-based Create/Update flow and fix any issues.

## Constraints
- Unit tests are mandatory.
- Manual testing is forbidden.
- Follow existing UI standards and architectural patterns.
- Do not modify code before user confirmation of the plan.

## Success Criteria
- Standalone agent UI correctly lists, opens, edits, and deletes leads.
- REST API endpoints in the `agent` sub-app are robust and feature-complete for leads.
- All unit tests pass.
- Backups are correctly performed.
