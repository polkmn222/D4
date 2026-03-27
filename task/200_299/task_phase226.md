# Phase 226 Task

- Scope: Phase 1 implementation for deterministic conversational CRUD in `development/ai_agent`.
- Approved objects: `lead`, `contact`, `opportunity`.
- Approved behavior:
  `CREATE -> OPEN_RECORD`,
  `UPDATE -> refreshed OPEN_RECORD`,
  deterministic query for `all leads`, `all contacts`, `recent opportunities`,
  safe fallback for ambiguous requests.
- Constraints: no manual testing, unit tests only, no service-gap fixes for `update_vehicle_spec` or `restore_template`.
