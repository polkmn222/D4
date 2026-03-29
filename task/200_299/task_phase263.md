# Phase 263 Task Record

## Request

Remove the following module trees from the active runtime and remove any Home dashboard buttons linked to them:

- `development/agent`
- `development/agent_gem`

## Approved Scope

- delete the `development/agent` module tree
- delete the `development/agent_gem` module tree
- remove Home dashboard buttons and asset references linked to those modules
- remove direct runtime mounts and dashboard fragment routes tied to those modules
- keep the rest of the application behavior unchanged
- add or update only the unit tests needed for this removal

## Constraints

- read project guidance under `development/docs/` and project-relevant files under `development/.codex/`
- do not inspect or rely on `Implementation`, `task`, `Walkthrough`, or `backups` while developing
- do only the explicitly requested work
- unit tests are mandatory
- manual testing is forbidden
- if ambiguity or risky follow-up work appears, report it before expanding scope
- back up only the changed module folders

## Notes

- The backup for this phase is stored under `backups/200_299/phase263/`.
- This phase record documents the current removal work only.
