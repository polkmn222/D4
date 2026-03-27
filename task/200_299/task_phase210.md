# Phase 210 Task

## Goal

Make the AI Agent visibly surface the lead form workspace in the agent UI and set debug mode to off by default.

## Scope

- Adjust AI Agent workspace placement and scroll behavior for form-opening flows.
- Set AI Agent debug mode default to off while preserving the manual toggle.
- Keep the change limited to AI Agent frontend modules and focused unit tests.

## Constraints

- Do not use SQLite for the final verification command selection.
- Do not introduce manual-test-only validation as the source of truth.
- Keep the existing lead form fetch/render contract intact unless the visibility fix requires minimal frontend changes.

## Verification

- Run focused unit tests that do not require switching the runtime to SQLite.
