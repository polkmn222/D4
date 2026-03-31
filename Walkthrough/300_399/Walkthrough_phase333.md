# Phase 333 Walkthrough

## What Changed

The grouped-object AI Agent `Edit` flow still depended on sending a natural-language `Manage ... edit` query. That made `Edit` feel too close to `Open`, because the intent still passed through the generic query/record-management path.

Phase 333 separates the two actions at the frontend entry point:

- `Open` still follows the record/open path
- `Edit` for `brand`, `model`, `asset`, and `message_template` now opens the inline edit form directly
- the same direct edit behavior is used from chat cards, selection actions, and the workspace header

This keeps the existing form UI but makes the action semantics explicit and consistent.

## Verification

- `PYTHONPATH=development pytest -m unit development/test/unit/ai_agent/frontend/test_ai_agent_continuity_dom.py -q`
- Result: `49 passed`

## Not Run

- Manual browser verification was not run by policy.
