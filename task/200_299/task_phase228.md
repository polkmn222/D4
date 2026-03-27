# Phase 228 Task

- Scope: documentation-and-test-infrastructure update only.
- Approved direction:
  keep pure mock-based AI-agent tests as unit tests,
  reclassify `SessionLocal` / `engine` / ORM-persistence tests as integration tests,
  use PostgreSQL only for DB-backed tests,
  introduce `TEST_DATABASE_URL`,
  add shared PostgreSQL fixtures and pytest markers.
- Constraints: no manual testing, no unrelated application logic changes, and do not change `development/db/database.py` in this phase.
