# Phase 218 Task

## Goal

Make the embedded lead create/edit screen usable through internal scrolling instead of growing the whole `Ops Pilot` panel around the web form.

## Scope

- Remove iframe auto-resize logic from the standalone agent frontend.
- Keep the right-side lead workspace fixed-height within the existing shell.
- Ensure the embedded web lead form scrolls inside the iframe.
- Update focused unit tests and docs for the revised frontend contract.

## Constraints

- Keep create/edit sourced from the real web lead routes.
- Do not switch to modal behavior.
- Validate with unit tests only.
