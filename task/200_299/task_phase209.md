# Phase 209 Task

## Goal

Add test-stage AI Agent debug instrumentation for the lead form workspace path so the user can see form-loading status inside the AI Agent UI without relying on manual debugging tools.

## Constraints

- Keep the work limited to the AI Agent lead form/workspace path.
- Do not use manual testing as the validation method.
- Do not make speculative business-logic changes without deterministic evidence.
- Preserve the existing `OPEN_FORM` contract unless a test-backed defect requires adjustment.

## Deliverables

- User-visible debug output for AI Agent workspace/form loading.
- Focused unit tests covering the debug instrumentation contract.
- Phase 209 backup for only the modified module folders.

## Verification

- Focused pytest run for the AI Agent form/workspace path.
