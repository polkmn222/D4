# Phase 316 Task Record

## Scope

Implement a minimal decision-layer eval integration for the local AI agent using `learning/eval_dataset_expanded.jsonl`.

## Requested Work

- Load `learning/eval_dataset_expanded.jsonl`.
- Send each row `user_input` through the local AI agent decision path.
- Compare actual decision output against:
  - `expected_object`
  - `expected_action`
  - `expected_tool`
  - `expected_retrieval_needed`
- Write structured eval results to a file.
- Add unit tests for the eval loader and comparison logic.

## Constraints

- Do not redesign the architecture.
- Do not add heavy end-to-end infrastructure.
- Keep scope limited to eval loading, decision execution, comparison, and result writing.
- Do not use SQLite.
- Do not use manual testing.
- Keep the solution server-side and Vercel-safe.
- Prefer a minimal adapter-style change over broad refactoring.

## Pre-Implementation Findings

- The repository guidance limits `.codex` reading to project-relevant files, while the user requested exhaustive `.codex` reading. Work proceeded using the repository-local scope rule plus the top-level `.codex` metadata files.
- The eval dataset labels do not match the runtime intent names one-to-one. A normalization layer is required to compare runtime output against eval labels such as `ASK_CLARIFICATION`, `REFUSE`, and tool labels like `crm_query`.

## Changed Module Folders

- `development/ai_agent/llm/backend`
- `development/test/unit/ai_agent/backend`
