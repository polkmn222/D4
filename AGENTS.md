# Agent Rules

Read project guidance in this order before work:
- `development/docs/agent.md`
- `development/docs/codex-working-rules.md`
- `development/docs/testing.md`
- other task-relevant files under `development/docs/`
- project-relevant files under `development/.codex/`

Do not inspect these folders unless the user explicitly asks:
- `Implementation`
- `task`
- `Walkthrough`
- `backups`

Stay inside the user's requested scope. Do not change application code, expand scope, or start implementation unless explicitly requested.

For future code changes:
- Unit tests are mandatory.
- Manual testing is forbidden.
- For each implementation phase, maintain four separate phase-labeled outputs:
  `Implementation/` for the implementation summary,
  `task/` for the task record,
  `Walkthrough/` for the walkthrough and verification notes,
  and `backups/` for backups of only the changed module folders.
- Back up only the module folders you change under `backups/<range>/phaseN/`.
- Do not back up untouched modules.

If you find ambiguity, suspicious behavior, likely bugs, risky code, or follow-up work not explicitly requested, stop and report it before changing code.
