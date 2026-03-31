# Phase 299 Task Record

## User Request
- Fix the opportunity create error:
  - `_force_null_fields` is an invalid keyword argument for Opportunity

## Work Done
- Patched `OpportunityService.create_opportunity(...)` so `_force_null_fields` is removed before ORM construction.
- Added a unit regression test for that exact leak.

## Notes
- Manual testing was not performed.
- SQLite was not used.
- Existing DB-backed CRUD test could not run because the configured Postgres host failed DNS resolution in this environment.
