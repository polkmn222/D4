# Task Phase 305: Conversational Intelligence & Robustness

## Request
- Boost success rate towards 80% via Cycle 2 of "Operation 80%".
- Implement conversational suggestions ("Did you mean?").
- Handle dialects and abbreviations.
- Fix SQL pluralization errors.

## Proposed Actions
1. Fix `traceback` import and harden `db.rollback()` logic.
2. Implement medium-similarity suggestions in `AiIntelligenceService`.
3. Add `TableAliasMapper` for SQL stability.
4. Seed Korean dialects and CRM shorthand.

## Approval
- Approved in session plan for Phase 305.
