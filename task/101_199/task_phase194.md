## Phase 194 Task

### Goal

Refine the MessageTemplate modal layout and make AI Agent create/update flows open the saved record reliably after save.

### Scope

- Move the MMS image field higher in the shared MessageTemplate modal.
- Improve AI Agent inline form save behavior so a successful create/update opens the saved record instead of relying on an extra chat turn.
- Keep regression coverage focused on layout order and inline-save workspace behavior.

### User-Reported Symptoms

- The MessageTemplate image upload area appeared too low in the modal.
- AI Agent create/update still did not feel like a true `open record` flow after save.
