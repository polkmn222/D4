# Phase 233 Walkthrough

## What Was Done
- The chat-native lead create/edit form now includes lookup controls for `product`, `model`, and `brand`.
- Each lookup control supports:
  - remote search
  - selecting a result
  - preloading the current value in edit mode
  - clearing the current selection
  - submitting the selected record ID

## How It Works
- Backend form schema now marks the three lead lookup fields with `control: lookup` and includes `lookup_object`.
- Lead edit responses preload `display_value` by resolving the saved IDs into readable names.
- Frontend chat form rendering now recognizes lookup fields and mounts a lightweight lookup UI that calls `/lookups/search`.
- On submit, the hidden ID field is posted through the existing AI-agent submit endpoint.
- Lead backend normalization still owns lookup dependency behavior after submit.

## How To Verify
- Run:
  - `PYTHONPATH=development pytest -m unit development/test/unit/ai_agent/backend/test_phase227_chat_native_open_form.py -q`
- Confirm the test file covers:
  - lead form schema lookup fields
  - edit preload of lookup display values
  - submit using IDs
  - frontend lookup renderer initialization

## Known Limitations
- This phase does not add recent-item lookup UX.
- This phase does not add live frontend dependency syncing between `product`, `model`, and `brand`.
- Backend normalization may still adjust related lead lookup values after submit.
