# Phase 319 Task

## Scope

Implement a narrow vector-retrieval path for message-sending rules so the AI agent can retrieve and answer policy-style questions using `learning/message_sending_rules_qdrant.json`.

## Approved Constraints

- Read and follow the active guidance under `development/docs/` and project-relevant `development/.codex/`.
- Do not inspect or use historical contents under `Implementation/`, `task/`, `Walkthrough/`, or `backups/` except for creating new phase outputs.
- Do not expand scope beyond message-sending-rules vector ingestion and AI-agent retrieval wiring.
- Unit tests are mandatory.
- Manual testing is forbidden.
- SQLite must not be used.
- If unexpected ambiguity, suspicious behavior, or additional required architectural work appears, report it before making extra changes.
- Back up only the module folders that are changed in this phase.

## Planned Changes

1. Extend the Qdrant service from connection-only behavior to collection management, upsert, and search helpers.
2. Add a narrow message-policy retrieval service that:
   - reads `learning/message_sending_rules_qdrant.json`
   - creates embeddings
   - upserts policy chunks into Qdrant
   - searches the indexed policy chunks
3. Add a narrow AI-agent retrieval path for message-sending policy questions only.
4. Add focused unit coverage for ingestion, retrieval, and AI-agent routing behavior.

## Success Criteria

- The repository contains a deterministic way to ingest `learning/message_sending_rules_qdrant.json` into Qdrant.
- The AI agent can use vector retrieval for message-sending policy questions without broadening other CRUD behavior.
- The retrieval path remains safe when vector configuration or credentials are unavailable.
- Focused unit tests pass without using SQLite or manual validation.
