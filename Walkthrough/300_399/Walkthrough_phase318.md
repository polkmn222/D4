# Phase 318 Walkthrough

## Overview

The first real batch run exposed an eval-runner stability gap: the adapter assumed `process_query()` would always return a dictionary. In practice, some runtime paths could still leave the adapter with a captured decision payload but a final `None` response.

The adapter was updated so it now:

- returns the live dictionary response when available
- falls back to the last captured `_execute_intent()` payload when the final response is `None`
- emits a safe `CHAT` stub only when neither source exists

## Validation

Executed:

- `PYTHONPATH=development pytest -m unit development/test/unit/ai_agent/backend/test_decision_eval.py -q`

Result:

- `7 passed`

## Batch Eval Result Summary

Full dataset totals:

- rows: `2000`
- full-match rows: `660`
- `expected_object` matches: `1305`
- `expected_action` matches: `875`
- `expected_tool` matches: `1066`
- `expected_retrieval_needed` matches: `1688`

Lowest full-match batches:

- `batch_1901_2000`: `1`
- `batch_1401_1500`: `6`
- `batch_1801_1900`: `6`
- `batch_1501_1600`: `13`

Highest full-match batches:

- `batch_0801_0900`: `58`
- `batch_1301_1400`: `58`
- `batch_0901_1000`: `51`

## Saved Outputs

- `learning/eval_results/batch_0001_0100.json` through `learning/eval_results/batch_1901_2000.json`
- `learning/eval_results/batch_index.json`
