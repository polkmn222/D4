# Phase 220 Task

## Goal

Make lead lookup fields work inside `Ops Pilot` by loading the shared web lead form together with its required assets.

## Scope

- Add a dedicated embedded lead page route.
- Render the shared lead form inside that page.
- Load shared lookup assets inside the embedded page.
- Point the standalone agent lead workspace to the new embedded page.
- Update focused unit tests and docs for the new iframe target contract.

## Constraints

- Keep the shared web lead form as the source of truth.
- Do not reintroduce a standalone custom lead form.
- Validate with unit tests only.
