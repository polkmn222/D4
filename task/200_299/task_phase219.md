# Phase 219 Task

## Goal

Keep lead lookup fields usable inside `Ops Pilot` while preserving the same shared web form contract.

## Scope

- Add an embedded rendering mode to the shared lead form route.
- Use that embedded mode from the standalone agent lead workspace.
- Remove modal-only close and height constraints in embedded mode only.
- Update focused unit tests and docs for the shared embedded-form contract.

## Constraints

- Keep create/edit sourced from the shared web lead form.
- Preserve lead lookup fields and their shared web lookup behavior.
- Validate with unit tests only.
