# Phase 299 Walkthrough

## Verification
- Command:
  - `PYTHONPATH=development pytest -m unit development/test/unit/crm/test_core_crud.py::test_create_opportunity_strips_force_null_fields_before_model_ctor -q`
- Result:
  - `1 passed`

## Constraint
- `development/test/unit/crm/test_core_crud.py::test_opportunity_crud` is currently blocked by external Postgres DNS resolution failure, not by the patched code path.
