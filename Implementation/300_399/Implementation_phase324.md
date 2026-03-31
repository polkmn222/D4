## Phase 324 Implementation

- Added deterministic existence-query routing for single-object English requests like:
  - `Is there any Lead for Tesla?`
- Added local creation-guidance responses for single-object English workflow requests like:
  - `Guide me through Lead creation`
- Kept both paths outside the full LLM ensemble and inside server-safe response shapes.
