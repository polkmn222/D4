# Testing Docs

This folder is the canonical source of truth for active testing structure and execution.

Start with `development/docs/testing.md` for the active repository-wide testing policy.

Test categories are split as follows:

- `development/test/unit/`: pure unit tests only
- `development/test/integration/`: PostgreSQL-backed tests only

- `strategy.md`: recommended test folder structure and organization rules.
- `migration_map.md`: mapping from current test files to the target structure.
- `coverage_matrix.md`: required coverage by object and shared feature area.
- `runbook.md`: recommended commands and execution order.
- `known_status.md`: current known failing tests, skipped tests, and interpretation notes.
- `manual_strategy.md`, `manual_checklist.md`, `manual_runbook.md`: historical references only. Manual testing is forbidden and these files must not be used as active instructions.

The old `development/test/docs/` archive set has been retired. Use the files in this folder as the active source of truth.

Imported skill docs under `docs/skills/**` can help with planning, but they are not the testing source of truth for D4.
