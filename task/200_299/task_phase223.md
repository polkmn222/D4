# Phase 223 Task

## Goal

Restore standalone New/Edit form visibility by handling iframe bootstrap loads correctly and tightening frontend coverage around the embedded loader state machine.

## Scope

- Ignore `about:blank` iframe bootstrap loads in the standalone embedded-form handler.
- Release pending state on fallback error paths.
- Strengthen standalone frontend contract tests for loader-state transitions.
- Update docs for the embedded-form loader behavior.

## Constraints

- Keep the standalone embedded lead form and post-save card architecture intact.
- Validate with unit tests only.
