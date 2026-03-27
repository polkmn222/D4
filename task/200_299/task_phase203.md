# Phase 203 Task

## Goal

Fix AI Agent lead explicit-ID CRUD so `show/edit/update/delete lead {id}` works consistently with the web lead CRUD flow, while keeping record IDs out of user-facing labels where not needed.

## Scope

- Update AI Agent lead intent resolution for explicit Salesforce-style IDs.
- Ensure delete parsing accepts 15/18-character lead IDs.
- Avoid record ID fallback in AI Agent open-record workspace titles.
- Add PostgreSQL-backed automated coverage and manual HTTP verification for explicit-ID lead CRUD.

## Out of Scope

- Lead create path `company_name` handling
- Non-lead object explicit-ID CRUD
