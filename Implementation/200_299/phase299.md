# Phase 299 Implementation

## Scope
- Fix opportunity create failure caused by `_force_null_fields` leaking into the ORM constructor.

## Changes
- Stripped `_force_null_fields` after opportunity create normalization and before `Opportunity(...)` construction.
- Added a focused unit test to ensure create does not pass `_force_null_fields` into the model constructor.

## Files
- `development/web/backend/app/services/opportunity_service.py`
- `development/test/unit/crm/test_core_crud.py`
