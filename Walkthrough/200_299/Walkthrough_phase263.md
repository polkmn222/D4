# Phase 263 Walkthrough

## What Was Done

The Home dashboard previously exposed two extra entry points:

- `Open Agent Gem`
- `Open Ops Pilot`

Those buttons depended on separate module trees under `development/agent_gem/` and `development/agent/`. The phase removed those module trees and then removed the runtime references that would otherwise keep pointing to deleted code.

The cleanup covered:

- dashboard button removal
- dashboard asset reference removal
- FastAPI sub-app mount removal
- dashboard panel route removal
- shared template-path cleanup
- unit-test cleanup and replacement assertions

## Resulting Runtime Shape

- `/ai-agent` remains mounted and unchanged
- `/agent` is no longer mounted
- `/agent-gem` is no longer mounted
- the Home dashboard no longer renders buttons for those removed surfaces

## Verification

Automated verification was run with:

```bash
PYTHONPATH=development pytest development/test/unit/web/frontend/test_gk_design_system.py development/test/unit/web/backend/app/test_perf_diagnostics.py development/test/unit/web/backend/test_runtime_path_alignment.py -q
```

## Verification Result

- `16 passed`

## Not Run

- no manual testing was run
- no broader unrelated suites were run because the requested scope was limited to removal of the two agent surfaces and their Home links
