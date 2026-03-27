# Phase 230 Task

## Request

Improve conversational list and query UX in `development/ai_agent`.

## Approved Scope

- Improve list/query UX for `lead`, `contact`, and `opportunity` only.
- Use the most recent AI-agent list result in conversation context first.
- Do not mix table-selection ordinals in this phase.
- If no usable ranked list context exists, return a narrow clarification.
- Do not guess silently.

## Constraints

- Keep the current create, update, and query contract unchanged.
- Use a feature branch by default.
- Unit tests only.
- No manual testing.
- Maintain `Implementation/`, `task/`, `Walkthrough/`, and `backups/` outputs for the phase.

## Explicit Safety Requirement

- Cross-object ordinal follow-up must not silently reuse the wrong list.
- Example: if the last list was leads, `open the first contact` must not silently use the lead list.
