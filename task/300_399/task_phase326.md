## Phase 326 Task

- Update Home tab `send recipients` and AI Agent `send recipients` flows for clearer, unified UI behavior.
- Enforce `Save Recipients` validation so it requires:
  - at least one selected recipient
  - and at least one message source from either a selected template or manually entered content
- Fix AI Agent template create form so fields render by type instead of showing every field.
- Align AI Agent template create/edit presentation with the web `template` new/edit format.
- Fix edit behavior for `brand`, `model`, `asset`, and `template` in AI Agent and verify CRUD coverage more carefully.
- Implement `asset.status` as a picklist in both web and AI Agent related UI paths.
- Restore or expose bulk delete for web send-object list view.
- Add AI Agent quick guide sections for recommended items and user recent activity, with support for pinning.
- Unify image-related button/UI behavior across web template new/edit/edit-button entry points, including immediate preview and clean removal behavior without leaving visible stale URL state.
- Add unit tests for all updated behaviors.
