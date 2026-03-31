# Phase 298 Implementation

## Scope
- Remove the AI Agent debug toggle from the header.
- Normalize maximize/minimize behavior for the AI Agent window.

## Changes
- Removed the `Debug On/Off` header button from the AI Agent panel.
- Forced debug UI state off by default in the front-end runtime.
- Simplified maximize layout to use fixed viewport insets instead of width/height calculations.
- Kept minimize behavior intact while preserving restore controls.
- Added DOM/source contract coverage for the new controls contract.

## Files
- `development/ai_agent/ui/frontend/templates/ai_agent_panel.html`
- `development/ai_agent/ui/frontend/static/js/ai_agent.js`
- `development/ai_agent/ui/frontend/static/css/ai_agent.css`
- `development/test/unit/ai_agent/frontend/test_ai_agent_continuity_dom.py`
