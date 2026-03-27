# Phase 221 Task

## Goal

After lead create/edit save in `Ops Pilot`, show the AI Agent-style open-record UI instead of leaving the embedded form visible.

## Scope

- Add a post-save open-card area to the standalone agent workspace.
- Enrich standalone agent lead detail payload for the open card.
- Reuse the AI Agent card visual pattern for the standalone agent summary.
- Replace the embedded `Save & New` action with `Cancel`.
- Route embedded cancel back to the standalone agent shell.
- Update focused unit tests and docs for the new contract.

## Constraints

- Keep the shared embedded web lead form as the edit/create source of truth.
- Keep validation unit-test-driven only.
- Limit the change to the standalone `agent` lead flow and shared embedded lead form footer behavior.
