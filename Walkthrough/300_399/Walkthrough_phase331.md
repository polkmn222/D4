# Phase 331 Walkthrough

## What Changed

The AI Agent maximize handler explicitly scrolled `#ai-agent-body` to the top whenever the panel entered maximized mode. That behavior matched the reported bug.

Phase 331 removes the forced top-scroll behavior and leaves the current chat/workspace scroll position untouched when maximize is toggled.

## Verification

- `PYTHONPATH=development pytest -m unit development/test/unit/ai_agent/frontend/test_ai_agent_continuity_dom.py -q`
- Result: `47 passed`

## Not Run

- Manual browser verification was not run by policy.
