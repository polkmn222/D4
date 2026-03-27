## Phase 193 Task

### Goal

Fix UI-level regressions that remained after the previous messaging and AI Agent changes.

### Scope

- Restore MMS image upload visibility in the generic MessageTemplate modal.
- Enforce exact create-route posting for shared modal forms.
- Prevent AI Agent delete confirmation buttons from triggering duplicate chat actions.
- Add automated regression coverage for modal rendering and MMS submission rules.

### User-Reported Symptoms

- MessageTemplate `New` and `Edit` modal did not show an image upload field after selecting `MMS`.
- AI Agent lead deletion still produced an extra follow-up chat response after confirming `Yes`.

### Constraints

- No manual testing.
- Keep changes limited to affected UI templates, routers, and regression tests.
