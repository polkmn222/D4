# Phase 319 Walkthrough

## What Was Added

This phase adds a narrow retrieval-only policy path for message-sending guidance.

The source data remains:

- `learning/message_sending_rules_qdrant.json`

The new flow is:

1. `MessagePolicyRetrievalService.sync_source_documents()` reads the JSON file.
2. The service creates embeddings with the OpenAI embeddings API.
3. The vectors are upserted into the configured Qdrant collection.
4. `AiAgentService.process_query()` detects policy-style message-sending questions.
5. Matching questions call the retrieval service and return a deterministic chat answer built from the top retrieved chunks.

## Runtime Boundaries

- The new retrieval path is intentionally narrow and does not change CRUD routing.
- Generic send-message actions still follow the existing messaging handoff path.
- If vector credentials or vector infrastructure are missing, the AI agent returns a safe explanatory message instead of pretending retrieval succeeded.
- No automatic boot-time indexing was introduced.

## Verification

Executed:

- `PYTHONPATH=development pytest -m unit development/test/unit/db/test_qdrant_service.py development/test/unit/ai_agent/backend/test_phase319_message_policy_retrieval.py -q`

Result:

- `15 passed`

## Not Executed

- Real OpenAI embedding calls
- Real Qdrant upsert/search against a live endpoint

These were not run because this phase used unit-only verification, manual testing is forbidden, and live vector credentials/endpoints were not part of the approved scope.
