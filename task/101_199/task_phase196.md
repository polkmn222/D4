## Phase 196 Task

### Goal

Stabilize MessageTemplate image registration and start the AI Agent CRUD refactor with a new object-specific backend module layout.

### Scope

- Add a new CRUD module folder under `development/ai_agent/ui/backend/`
- Move lead-specific response contracts into a dedicated lead module
- Verify and fix MessageTemplate image flows:
  - upload
  - type switch away from `MMS`
  - clear-image
  - detail rendering

### Current Strategy

- Start with `lead` only
- Reuse the same contract pattern for other objects after lead behavior is confirmed
