# Phase 206 Walkthrough

The lead create/edit form response was returning `OPEN_FORM`, but after `Reset Agent` the chat body was rebuilt from `AI_AGENT_DEFAULT_BODY_HTML`. That template did not include the AI Agent workspace DOM, so `openAgentWorkspace()` had nowhere to render the form.

The default body HTML now includes the same workspace container structure as the loaded panel template, so create/edit can open the form panel even after reset.
