# Phase 340 Task

## Scope

Update the active runtime docs for the phase 319 message-policy vector retrieval path, then verify runtime configuration and run the explicit policy-ingestion flow.

## Approved Constraints

- Keep the scope limited to documentation updates plus runtime configuration and ingestion for message-policy retrieval.
- Do not broaden the implementation surface beyond the message-policy vector path.
- Manual testing is forbidden.
- Do not use SQLite.
- If runtime configuration is missing or live ingestion fails, report the exact blocker without making unrelated code changes.

## Planned Work

1. Update the relevant active docs to describe the narrow message-policy retrieval path and its deployment/runtime requirements.
2. Check the required environment variables for embeddings and Qdrant access.
3. Run the explicit ingestion path for `learning/message_sending_rules_qdrant.json`.
4. Record the outcome in the phase walkthrough.

## Success Criteria

- Active docs mention the message-policy vector retrieval path accurately.
- Runtime configuration is checked explicitly.
- The ingestion path is executed or any concrete runtime blocker is reported.
