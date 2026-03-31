# Task Phase 303: DB-Driven AI Intelligence Store

## Request
- Move AI intent patterns and synonyms from static code/files to PostgreSQL.
- Implement similarity mapping for better failure handling.
- Enable dynamic updates of agent intelligence.

## Proposed Actions
1. Add `AiIntentPattern` and `AiSynonym` models to `models.py`.
2. Seed DB with "Hall of Fame" prompts and existing mappings.
3. Integrate DB lookup into `IntentPreClassifier`.

## Constraints
- No SQLite.
- Maintain existing core object logic.
- Target PostgreSQL `pg_trgm` for similarity.

## Approval
- Approved in session plan for Phase 303.
