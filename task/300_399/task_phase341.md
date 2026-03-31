# Phase 341 Task

## Request

Remove all Solapi-related code, tests, configuration references, and active documentation from the repository.

## Scope

- Remove the Solapi messaging provider implementation.
- Remove Solapi-specific provider selection and status reporting.
- Update deployment and messaging documentation to reflect the active SureM and relay runtime.
- Update focused unit tests for the provider changes.

## Constraints

- Do not inspect historical phase contents as implementation reference.
- Do not run manual tests.
- Use unit tests only.
- Do not introduce SQLite-based verification.

## Success Criteria

- No active `solapi` references remain in code, tests, or active docs.
- Messaging provider selection still supports `mock`, `slack`, `surem`, and `relay`.
- Focused messaging unit tests pass.
