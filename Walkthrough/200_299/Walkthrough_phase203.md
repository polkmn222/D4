# Phase 203 Walkthrough

## Problem

AI Agent did not treat explicit lead IDs as direct CRUD targets. `show/edit/update/delete lead {id}` fell through to generic guidance or list query behavior, and open-record tabs could expose raw IDs as fallback titles.

## Fix

1. Added an explicit lead-ID parser before the generic classifier path.
2. Routed each explicit action to the correct lead behavior:
   - show/open/view -> open record
   - edit -> open edit form
   - update -> apply update and reopen record
   - delete -> delete immediately
3. Updated delete detection so Salesforce-style 15/18-character IDs are recognized.
4. Changed AI Agent open-record tab titles to use the record/chat-card title instead of raw IDs.

## Outcome

- AI Agent now handles lead explicit-ID CRUD naturally.
- User-facing messages and workspace titles do not need to expose the raw lead ID.
- PostgreSQL-backed automated and manual verification passed for the explicit-ID lead CRUD flow.
