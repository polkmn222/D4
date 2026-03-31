# Phase 331 Implementation

## Summary

- Removed the forced `scrollTo({ top: 0 })` call from `maximizeAiAgent()` in the AI Agent frontend.
- Added a DOM-level unit test that verifies maximize preserves the current scroll position while still toggling the maximized class.

## Changed Modules

- `development/ai_agent/ui/frontend/static/js`
- `development/test/unit/ai_agent/frontend`
