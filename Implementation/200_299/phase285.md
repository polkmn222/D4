Phase 285 Implementation

- Reworked AI Agent jump-button visibility to use bottom proximity instead of mixed anchor visibility heuristics.
- Made `OPEN_FORM` with `form_url` render the inline web form shell in chat instead of opening the workspace directly.
- Applied form field `layout` metadata in the inline schema renderer so lead parity can use half-width lookup rows and full-width description.
- Replaced raw-ID delete success copy with object-aware human labels for lead, contact, opportunity, product, asset, brand, model, and message template.
