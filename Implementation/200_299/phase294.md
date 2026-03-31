# Phase 294 Implementation

- restored deterministic pre-LLM handling for `AI Recommend` and `Change AI Recommend`
- restored AI Agent inline web-form submit continuity for lead/contact/opportunity by routing supported modal submits through the AI Agent submit bridge
- fixed recent-opportunity boundary handling so recent-created opportunity prompts resolve to query behavior instead of accidental create
- added `New` to AI Agent result-table actions
- aligned opportunity `status` to picklist behavior in both AI Agent and web modal forms
