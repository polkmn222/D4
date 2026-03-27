# Phase 211 Task

## Goal

Strengthen AI Agent frontend unit coverage for workspace visibility behavior and update the active markdown docs to reflect the current AI Agent lead workspace behavior and focused test status.

## Scope

- Add frontend-focused unit tests for AI Agent workspace placement, scrolling, and debug default behavior.
- Update runtime/testing markdown docs affected by the recent AI Agent frontend changes.
- Keep the change limited to tests and docs for this phase.

## Constraints

- Do not weaken existing test coverage while moving assertions toward frontend-focused ownership.
- Keep PostgreSQL as the active runtime assumption in the docs.
- Do not use manual testing as the validation source of truth.

## Verification

- Run focused frontend-safe AI Agent unit tests.
