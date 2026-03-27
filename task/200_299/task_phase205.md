# Phase 205 Task

## Goal

Reduce AI Agent lead create/edit latency and ensure lead form requests open an actual form surface instead of only showing a chat message.

## Scope

- Add fast-path lead form resolution to avoid unnecessary LLM calls for common create/edit requests.
- Change AI Agent `OPEN_FORM` frontend handling to open the workspace form directly.
- Add unit coverage for the fast-path and workspace-open behavior.
