# Phase 197 Implementation Plan

## Planned Changes

1. Update AI Agent inline-form submit handling to normalize success and failure messaging and always open the saved record in-chat on successful save flows that redirect to a record detail page.
2. Change the message-template modal image flow so file selection stays client-side until template save, then upload and persist only during the save transaction.
3. Add focused unit tests for the AI Agent save-to-open contract and the deferred template-image persistence contract.

## Modules Expected To Change

- `development/ai_agent/ui/`
- `development/web/frontend/static/js/`
- `development/web/message/backend/`
- `development/test/unit/ai_agent/backend/`
- `development/test/unit/web/message/backend/`

## Verification

- Run focused `pytest` commands for the touched AI Agent and messaging test files.
