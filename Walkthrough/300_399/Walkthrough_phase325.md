## Phase 325 Walkthrough

### Verification

Executed:

```bash
PYTHONPATH=development pytest -m unit \
  development/test/unit/ai_agent/backend/test_phase321_english_deterministic_query.py \
  development/test/unit/ai_agent/backend/test_phase322_bounded_cerebras_clarification.py \
  development/test/unit/ai_agent/backend/test_phase230_query_context.py -q
```

Result:

- `20 passed`

### Notes

- No manual testing was performed.
- `Which <object> is hot?` and `Help with <object> flow` now resolve locally to guidance `CHAT` responses.
