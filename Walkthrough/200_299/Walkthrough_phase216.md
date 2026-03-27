# Phase 216 Walkthrough

## Goal

Make the standalone `Ops Pilot` agent use the same lead create/edit surface as the main web app, so the full lead field set comes from the existing web implementation instead of a custom reduced agent form.

## What Changed

- Replaced the custom standalone lead form with a workspace shell.
- Embedded the real web lead form route inside the shell:
  - create: `/leads/new-modal`
  - edit: `/leads/new-modal?id=<lead_id>`
- Added iframe load handling so the shell can detect save completion after the web route redirects to `/leads/<id>`.
- Kept delete inside the standalone agent API flow, with confirmation.

## Why

- The web lead form is already the source of truth for all lead fields.
- Reusing that route avoids field drift between web and agent.
- It also removes the extra custom save path that was making the standalone agent feel slower than the web flow.

## Validation

- `node --check development/agent/ui/frontend/static/js/app.js`
- `PYTHONPATH=development pytest development/test/unit/agent/test_runtime_contract.py development/test/unit/agent/test_frontend_contract.py -q`
- Result: `13 passed`
