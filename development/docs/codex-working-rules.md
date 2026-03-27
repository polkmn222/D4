# Codex Working Rules

## Purpose

This document defines how Codex should operate inside the D5 repository.

## Reading Order

Before making changes, read guidance in this order:

1. `development/docs/agent.md`
2. `development/docs/codex-working-rules.md`
3. `development/docs/testing.md`
4. other task-relevant files under `development/docs/`
5. project-relevant files under `development/.codex/`

When the task is specifically about testing, also read the active files under `development/docs/testing/`.

## Excluded Directories

Do not read, inspect, summarize, or use files from these folders unless the user explicitly asks:

- `Implementation`
- `task`
- `Walkthrough`
- `backups`

This exclusion applies to both direct inspection and broad discovery commands.

## `.codex` Reading Scope

Do not exhaustively read the generic skill library under `development/.codex/`.

Treat `.codex` review as limited to:

- project-relevant metadata
- local config
- local instructions
- files directly referenced by active project docs

If a `.codex` subtree is generic, external, or unrelated to the active task, do not bulk-read it.

## Scope Control

- Do only what the user explicitly requested.
- Do not expand scope because a related improvement seems useful.
- Do not change application code during a documentation-only task.
- Do not introduce a new framework or parallel runtime unless explicitly requested.
- If the user asks for planning only, do not implement.

## Reporting Rule

If you find any of the following, stop and report them before modifying code:

- ambiguity
- suspicious behavior
- likely bugs
- risky code paths
- missing services or handlers
- architectural changes that seem necessary but were not explicitly requested

The report should separate observed facts from proposed follow-up work.

## Backup Rule For Future Code Changes

When a future task includes code changes:

- back up only the changed module folder
- do the backup before editing that module
- preserve the original relative repository path under `backups/<range>/phaseN/`
- do not back up untouched modules

Documentation-only work does not require code-module backups unless the user explicitly asks for them.

## Testing Rule

- Unit tests are mandatory for future logic or behavior changes.
- Manual testing is forbidden.
- Do not use browser checks, click-through verification, or ad hoc runtime probing as substitutes for automated tests.
- If a task is documentation-only, do not invent test execution just to satisfy a code-change rule.

## `development/ai_agent` Execution Expectations

For future work in `development/ai_agent`:

- keep the mounted runtime under `development/ai_agent`
- reuse existing services under `development/web/backend/app/services/` and `development/web/message/backend/services/`
- prefer deterministic parsing and CRUD handling before LLM fallback
- keep response shapes aligned with the frontend contract

See `development/docs/ai-agent-crud-contract.md` for the behavior contract.
