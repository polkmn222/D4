Phase 287 Implementation

- Extended inline web-form precedence to all AI Agent `OPEN_FORM` responses when `form_url` is available.
- Added deterministic edit-form routing for fast-form objects: product, asset, brand, model, and message template.
- Added asset lookup display fallback from `name` to `vin`.
- Added multi-object CRUD contract tests for edit-form routing and delete-copy behavior.
