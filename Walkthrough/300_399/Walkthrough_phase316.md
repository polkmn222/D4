# Phase 316 Walkthrough

## Overview

This phase adds a lightweight evaluation harness for the AI agent decision layer.

The harness uses the existing `AiAgentService.process_query()` entry point. For requests that normally proceed into `_execute_intent()`, the eval layer captures the pre-execution decision payload so the report reflects the decision path rather than downstream CRUD side effects.

## Result Structure

The generated JSON report includes:

- dataset metadata
- run timestamp
- per-row expected values
- per-row normalized actual values
- per-row field-by-field comparison results
- summary match counts

## Validation

Executed:

- `PYTHONPATH=development pytest -m unit development/test/unit/ai_agent/backend/test_decision_eval.py -q`

Result:

- `5 passed`

## Local Run

Example command:

```bash
PYTHONPATH=development python -m ai_agent.llm.backend.decision_eval \
  --dataset learning/eval_dataset_expanded.jsonl \
  --output learning/eval_results/decision_eval_local.json
```

Optional smaller run:

```bash
PYTHONPATH=development python -m ai_agent.llm.backend.decision_eval \
  --dataset learning/eval_dataset_expanded.jsonl \
  --output learning/eval_results/decision_eval_sample.json \
  --limit 50
```
