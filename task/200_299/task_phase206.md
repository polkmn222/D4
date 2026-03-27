# Phase 206 Task

## Goal

Fix AI Agent create/edit form opening after reset so the form workspace still exists and `OPEN_FORM` can render an actual tab/panel.

## Scope

- Restore AI Agent workspace markup inside the default body HTML used by reset.
- Add unit coverage to prevent workspace DOM regression after reset.
