# Phase 321 Task Record

## Scope

Implement the first English-first deterministic improvements identified from the eval analysis.

## Requested Work

- improve typo and alias normalization for English CRM requests
- improve deterministic handling for search/find/pull/export style query requests
- improve deterministic handling for `latest` / `last` read-edit phrases by routing them to safe recent-list queries
- keep destructive and ambiguous execution safety unchanged

## Constraints

- keep the changes narrow
- prefer deterministic normalization over broader LLM expansion
- do not weaken safety gates for update or delete execution

## Changed Module Folders

- `development/ai_agent/llm/backend`
- `development/ai_agent/ui/backend`
- `development/test/unit/ai_agent/backend`
