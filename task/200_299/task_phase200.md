# Phase 200 Task

## Scope

- Fix the canonical lead create path so PostgreSQL-backed lead creation works again.
- Verify that AI Agent lead creation can now complete because it depends on the same create service path.
- Validate with focused unit tests and PostgreSQL-backed manual checks.

## Constraints

- Keep changes limited to the lead create path and its direct tests.
- Use unit tests first, then PostgreSQL-backed manual validation.
- Do not change unrelated scripts such as archived utility files unless they are proven necessary.

## Success Criteria

- `POST /leads/` no longer fails with `_force_null_fields`.
- AI Agent lead create can return a valid open-record contract after persistence.
- PostgreSQL-backed manual validation confirms web create, web edit, and AI Agent create flows.
