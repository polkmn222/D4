# Phase 314 Task Record

## Scope

- Verify and harden the new DB-backed AI intelligence path added around phases 303-306.
- Repair prompt seeding so it can use learning artifacts that still exist in the repository.
- Align test collection so PostgreSQL-backed CRUD checks do not run under `-m unit`.

## Constraints

- Stay within the reported issues only.
- Do not use manual testing.
- Keep PostgreSQL as the only supported DB target for DB-backed checks.
- Add focused automated tests for the new safety behavior.

## Approved Execution

- User explicitly authorized follow-up implementation after the review findings.

## Success Criteria

- AI intelligence lookup does not break normal agent flow when optional DB objects or `pg_trgm` are unavailable.
- The mass-seed script no longer depends solely on the deleted `learning/agent.txt`.
- `development/test/unit/crm/test_core_crud.py` is excluded from `pytest -m unit`.
- Focused automated tests pass.
