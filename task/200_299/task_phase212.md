# Phase 212 Task

## Goal

Refactor the AI Agent frontend so lead form flows use an AI Agent-local modal presentation that more closely matches the main web experience.

## Scope

- Add an agent-local form modal container in the AI Agent frontend.
- Route AI Agent form-opening flows to that modal presentation.
- Keep record/detail workspace behavior for non-form content unless the new modal path explicitly replaces it.
- Update focused unit tests and active docs for the new runtime contract.

## Constraints

- Keep PostgreSQL as the active runtime assumption.
- Do not rely on manual testing as the source of truth.
- Limit the runtime change to AI Agent frontend behavior and directly affected docs/tests.

## Verification

- Run focused AI Agent unit tests that validate the new form-modal runtime contract.
