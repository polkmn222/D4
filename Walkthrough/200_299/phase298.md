# Phase 298 Walkthrough

## Verification
- Command:
  - `PYTHONPATH=development pytest -m unit development/test/unit/ai_agent/frontend/test_ai_agent_continuity_dom.py -q`
- Result:
  - `39 passed`

## Outcome
- The AI Agent header no longer shows the debug toggle.
- Maximize now uses a more stable fixed-inset viewport layout.
