# Phase 188 Task

## Objective

Align the active repository with the current `development/` application root so the runtime, tests, and canonical documentation all reference the same folder structure.

## Requested Constraints

- Do not read historical phase content from `task/`, `Implementation/`, `Walkthrough/`, or backup folders.
- Store this phase in the current grouped range with the shared phase number `188`.
- Back up only the modules and files that are modified in this phase under `backups/101_199/phase188/`.
- Do not perform manual testing.
- Add or maintain unit-test coverage for every changed behavior.
- If a suspicious condition, architecture concern, or unexpected error appears, stop short of speculative code changes and report it clearly.

## Scope

1. Fix runtime path references that still point to `.gemini/development` even though the active code now lives under `development/`.
2. Update canonical docs so they describe the current folder structure accurately.
3. Update affected automated tests so they use the current application root.
4. Verify that `run_crm.sh` starts the application using the active structure.
5. Run unit tests relevant to the changed modules, then run the full unit suite if targeted validation passes.

## Out of Scope

- Behavioral feature changes unrelated to the active folder-structure migration.
- Manual smoke checks, manual runbooks, or browser-based validation.
- Editing historical phase artifacts.

## Success Criteria

- `run_crm.sh` resolves the active application root correctly.
- Runtime entry points and deployment configuration no longer depend on the removed `.gemini/development` path.
- Unit tests pass for the changed runtime and path-sensitive areas.
- Canonical docs describe the current `development/` layout consistently.
- Modified modules are backed up in `backups/101_199/phase188/` before execution changes.
