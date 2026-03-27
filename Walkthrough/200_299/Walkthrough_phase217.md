# Phase 217 Walkthrough

## Goal

Reduce clipping in the standalone `Ops Pilot` lead workspace when the real web lead create/edit screen is embedded inside the agent shell.

## What Changed

- The `Ops Pilot` window now uses a near-fullscreen fixed layout on desktop.
- The sidebar was narrowed so the lead workspace gets more room.
- The embedded iframe now measures the loaded document and updates its own height.
- The shell keeps a larger minimum workspace height across desktop and mobile breakpoints.

## Why

- The embedded web lead form contains many fields and section blocks.
- A smaller fixed iframe made the form appear cut off even though the route itself was working.
- Resizing the shell and synchronizing iframe height keeps the web form readable while preserving the non-modal agent surface.

## Validation

- `node --check development/agent/ui/frontend/static/js/app.js`
- `PYTHONPATH=development pytest development/test/unit/agent/test_runtime_contract.py development/test/unit/agent/test_frontend_contract.py -q`
