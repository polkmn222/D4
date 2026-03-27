# Implementation Phase 224: Fix Standalone Agent CRUD UI and REST API

## Proposed Changes

### 1. Backend: `development/agent/ui/backend/router.py`
- Expand `LeadPayload` to include all Lead fields: `gender`, `brand`, `model`, `product`.
- Ensure all fields in `LeadPayload` are optional with default `None` or empty string as appropriate.
- Update `update_lead` (PATCH) to use `payload.model_dump(exclude_unset=True)` to support true partial updates.
- Ensure the `POST` and `PATCH` endpoints correctly pass all fields to `LeadService`.

### 2. Testing: `development/test/unit/agent/test_router.py`
- Update existing tests to verify that `brand`, `model`, `product`, and `gender` are correctly handled.
- Add a test case for `PATCH` to confirm that it does NOT overwrite unspecified fields with defaults (using `exclude_unset=True`).
- Ensure all tests pass with the new implementation.

### 3. Documentation: `development/docs/agent.md`
- Ensure the runtime notes reflect the improved REST API capabilities for the standalone agent.

## Execution Plan
1.  Modify `development/agent/ui/backend/router.py` with the updated `LeadPayload` and `PATCH` logic.
2.  Run the newly created unit tests in `development/test/unit/agent/test_router.py`.
3.  Verify that no regressions are introduced in existing agent tests.
4.  Finalize the implementation and create the walkthrough.

## Verification Strategy
- **Unit Tests**: `PYTHONPATH=development pytest development/test/unit/agent/test_router.py`
- **Contract Tests**: `PYTHONPATH=development pytest development/test/unit/agent/test_runtime_contract.py`
- **Manual Verification**: Not allowed.
