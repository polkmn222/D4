# Phase 228 Walkthrough

- What was done: the test tree now distinguishes pure unit tests from PostgreSQL-backed integration tests, and the identified AI-agent DB tests were moved into `development/test/integration/ai_agent/backend/`.
- How it works: integration tests use `TEST_DATABASE_URL`, the integration conftest exports it as `DATABASE_URL`, and shared PostgreSQL fixtures provide transaction-scoped sessions.
- How to verify:
  run `PYTHONPATH=development pytest -m unit development/test/unit`
  and run `TEST_DATABASE_URL=postgresql://... PYTHONPATH=development pytest -m integration development/test/integration`.
- Remaining blocker: import-time DB initialization in `development/db/database.py` still requires a real database URL before some imports.
- Backup reference: `backups/200_299/phase228/`
