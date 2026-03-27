# Phase 209 Implementation Plan

## Scope

- Investigate why AI Agent lead create/edit requests return the chat message for opening a form, but the actual form workspace is not visibly rendered to the user.
- Limit the investigation to the AI Agent lead form path and its directly related modules.
- Do not perform manual testing.
- Do not change runtime behavior until the investigation path is approved.

## In-Scope Modules

- `development/ai_agent/ui/frontend/static/js/ai_agent.js`
- `development/ai_agent/ui/frontend/static/css/ai_agent.css`
- `development/ai_agent/ui/frontend/templates/ai_agent_panel.html`
- `development/ai_agent/ui/backend/service.py`
- `development/ai_agent/ui/backend/crud/lead.py`
- `development/web/backend/app/api/form_router.py`
- Related unit tests under `development/test/unit/ai_agent/` and `development/test/unit/web/`

## Current Observations

- The backend still returns the `OPEN_FORM` contract for lead create/edit flows.
- The frontend still routes `OPEN_FORM` to `openAgentWorkspace(data.form_url, data.form_title || 'Form')`.
- The visible failure appears to be runtime rendering behavior, fetch/render error handling, or a missing automated assertion for the real workspace visibility contract.
- Static reading alone is not sufficient to prove the root cause safely.

## Planned Work

1. Add focused unit coverage for the lead form workspace path so the intended runtime contract is testable without manual reproduction.
2. Inspect the AI Agent form loading path for silent failure points in:
   - workspace open
   - HTML extraction for `/leads/new-modal`
   - script rehydration
   - form container wiring
3. If unit-test-backed evidence identifies a concrete defect, patch only the minimal affected module.
4. Add or update unit tests that fail before the fix and pass after the fix.
5. Keep the change set limited to the lead workspace rendering path.

## Guardrails

- No manual test steps.
- No speculative runtime fix without a concrete, test-backed defect.
- If the investigation reveals a broader architectural issue or ambiguous behavior, stop and report before changing code.
- Back up only the actually modified module folders if execution is approved.

## Verification Plan

- Run focused unit tests for the AI Agent lead workspace/form path.
- Run any adjacent unit tests needed to confirm the lead form contract did not regress.
- Do not use browser-only verification for this phase.

## Expected Deliverable After Approval

- A minimal fix for the confirmed lead workspace visibility defect, if a deterministic defect is identified.
- Focused unit test coverage proving the lead create/edit workspace contract.
