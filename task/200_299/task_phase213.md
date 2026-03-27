# Phase 213 Task

## Goal

Implement a brand-new mounted `agent` application with its own `llm` and `ui` folder structure, a standalone frontend, and lead CRUD functionality, then add a new dashboard button above the existing AI Agent entry.

## Scope

- Create the new `development/agent/` runtime structure.
- Mount the new sub-app under `/agent`.
- Add a new lazy-loaded panel route for the dashboard.
- Implement a standalone frontend in `agent/ui` and lead CRUD API endpoints for the new agent.
- Add the new dashboard button above the existing AI Agent button.

## Constraints

- Do not reuse the existing AI Agent runtime code as the implementation base.
- Keep PostgreSQL as the active runtime assumption.
- Use unit tests only for validation.

## Verification

- Run focused unit tests for the new agent frontend contract and backend route/module contract.
