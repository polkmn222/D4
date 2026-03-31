## Phase 303 Walkthrough

1. Raised the base AI Agent height to make the in-chat messaging composer usable without maximize.
2. Changed the Send Message composer to render as:
   - one column by default
   - preview-enabled two-column layout only when maximized
3. Added front-end validation so the composer does not attempt a send with empty content/template or MMS without an image-backed template.
4. Tied active send composer rendering to `isAiAgentMaximized` so changing window size updates the layout immediately.

### Verification

- `PYTHONPATH=development pytest -m unit development/test/unit/ai_agent/frontend/test_ai_agent_continuity_dom.py -q`
  - `43 passed`
