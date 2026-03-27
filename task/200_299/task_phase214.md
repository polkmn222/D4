# Phase 214 Task

## Goal

Fix the intermittent standalone agent panel visibility issue, prevent save/refresh flows from getting stuck in a loading state, and require delete confirmation before removing a lead.

## Scope

- Fix `Ops Pilot` open/toggle behavior.
- Add request-state handling and error recovery for save and refresh flows.
- Add explicit delete confirmation.
- Update focused unit tests and active docs if the runtime contract changes.

## Constraints

- Keep the changes limited to the standalone `agent` surface and directly related docs/tests.
- Use unit tests only for verification.
