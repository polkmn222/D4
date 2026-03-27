# Phase 198 Task

## Scope

- Reconcile the clarified requirement for template image persistence.
- Confirm that template images do not upload on selection, but do upload and save to the database when the user presses `Save`.
- Keep Home tab `Send Message` and template-detail CRUD behavior aligned.

## Constraints

- Do not change unrelated flows.
- Manual testing is forbidden.
- Use focused unit tests only.
- Preserve phase tracking and targeted backups.

## Success Criteria

- Selecting a template image keeps the change local until `Save`.
- Pressing `Save` uploads the image, stores attachment metadata in the database, and keeps template CRUD intact.
- The same behavior exists in both the Home tab `Send Message` template modal and the template detail/edit flow.
