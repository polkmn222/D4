# Phase 216 Task

## Goal

Convert `Ops Pilot` into a lead-first shell that uses the real web lead form routes instead of a custom standalone lead form.

## Scope

- Remove the custom lead form UI from the standalone agent frontend.
- Embed the real web lead create/edit screen for lead flows.
- Keep the standalone agent focused on lead-first behavior for this phase.
- Update focused unit tests and docs for the embedded web-form contract.

## Constraints

- Use the existing web lead routes as the actual form runtime.
- Keep validation unit-test-driven.
- Limit the change to the standalone `agent` surface and related docs/tests.
