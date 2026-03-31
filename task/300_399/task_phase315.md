# Phase 315 Task

## Scope

- Add a minimal Qdrant connection service for the active runtime.
- Add unit tests for environment loading and client construction behavior.
- Add the required Python dependency for Qdrant client usage.

## Constraints

- Keep the change limited to connection setup only.
- Do not add embedding, indexing, retrieval, or AI-agent integration yet.
- Manual testing is forbidden.
- SQLite must not be introduced.
- Do not update unrelated runtime behavior.

## Approvals

- The user approved proceeding with code and test changes.
- The user allowed minimal inspection of phase-tracking folders to assign a new phase number and create required artifacts.

## Success Criteria

- `QDRANT_ENDPOINT` and `QDRANT_API_KEY` are read through a dedicated service.
- The service can build a `QdrantClient` instance.
- Unit tests cover missing env handling and client construction without requiring network access.
