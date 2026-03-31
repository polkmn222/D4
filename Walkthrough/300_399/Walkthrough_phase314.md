# Phase 314 Walkthrough

## What Changed

- `AiIntelligenceService.find_best_matching_pattern()` and synonym lookup now return a safe no-op result when optional AI intelligence tables or the PostgreSQL `similarity()` function are unavailable, instead of breaking the main agent flow.
- `seed_mass_patterns_phase304.py` now searches for an available prompt source in `learning/` and supports the current `**N. Q: \`...\`**` markdown format.
- `development/test/conftest.py` now preserves explicit `integration` marks, so `pytest -m unit` no longer runs `test_core_crud.py`.

## Verification

- Passed: `PYTHONPATH=development pytest -m unit development/test/unit/db/test_ai_intelligence_service.py development/test/unit/db/test_database_runtime_contract.py development/test/unit/web/message/backend/test_message_send_limits.py development/test/unit/ai_agent/backend/test_phase269_multi_object_deterministic.py development/test/unit/ai_agent/backend/test_phase279_noisy_alias_and_clarification_contract.py development/test/unit/ai_agent/backend/test_lead_crud_module.py -q`
- Passed: `PYTHONPATH=development pytest -m unit development/test/unit/crm/test_core_crud.py -q -rs`
  Result: `10 deselected`

## Not Run

- PostgreSQL integration suites were not run because `TEST_DATABASE_URL` was not set in the current environment.
- Real DB verification of the new intelligence tables could not be completed in this session for the same reason.
