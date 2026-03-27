# Phase 205 Walkthrough

Two factors were making lead create/edit feel slow or incomplete inside AI Agent.

1. Some natural-language create/edit requests were missing the rule-based shortcuts and falling through to the multi-LLM ensemble, which adds network latency.
2. `OPEN_FORM` only appended a chat message and then tried to render an inline form. If that second step lagged or failed, the user only saw the message.

The fix adds a direct lead form fast-path in the backend and makes the frontend open the form in the AI Agent workspace immediately when `OPEN_FORM` is returned.
