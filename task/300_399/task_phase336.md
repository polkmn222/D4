## Phase 336 Task

- Scope: fix message template deletion when the template still references an uploaded image attachment.
- Target surfaces:
  - web template delete
  - AI Agent template delete
- Constraint:
  - keep the fix inside the shared delete service used by both paths
