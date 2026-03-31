## Phase 322 Implementation

- Added English request-wrapper unwrapping in `AiAgentService.process_query()` for deterministic routing.
- Added bounded explanatory clarification handling in `AiAgentService` that:
  - triggers only for single-object English explanatory requests,
  - calls Cerebras only for `CHAT` clarification generation,
  - validates/sanitizes the Cerebras response,
  - falls back to a local clarification response when Cerebras is unavailable or invalid.
- Added unit tests for wrapped deterministic queries and bounded clarification behavior.
