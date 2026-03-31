## Phase 324 Walkthrough

### Verification

Executed:

```bash
PYTHONPATH=development pytest -m unit \
  development/test/unit/ai_agent/backend/test_phase321_english_deterministic_query.py \
  development/test/unit/ai_agent/backend/test_phase322_bounded_cerebras_clarification.py \
  development/test/unit/ai_agent/backend/test_phase230_query_context.py -q
```

Result:

- `18 passed`

### Notes

- No manual testing was performed.
- `is there any ... for ...` now routes to query with `search_term`.
- creation guidance remains a `CHAT` response and does not auto-execute create.
