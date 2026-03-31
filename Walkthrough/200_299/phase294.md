# Phase 294 Walkthrough

- `AI Recommend` and `Change AI Recommend` now resolve before LLM fallback so the AI Agent no longer returns generic recommendation questions for those direct commands
- supported inline web-form submits for lead/contact/opportunity now use the AI Agent submit path, restoring `OPEN_RECORD` continuity instead of generic `Record saved successfully`
- recent-created opportunity requests now map to query intent before create intent
- AI Agent tables now expose `New` alongside `Open`, `Edit`, and `Delete`
- opportunity `status` now renders as a select in both AI Agent and web modal forms

## Verification

- focused unit/DOM run: `113 passed`
- broader AI Agent/web regression run: `127 passed`
