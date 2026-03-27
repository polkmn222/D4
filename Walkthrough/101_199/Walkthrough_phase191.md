# Phase 191 Walkthrough

## Summary

This phase made deployment behavior safer by blocking direct Solapi delivery on Vercel by default and documenting the intended Render-first production shape for carrier messaging.

## What Changed

- Solapi delivery is now blocked automatically when the runtime detects Vercel, unless `ALLOW_SOLAPI_ON_VERCEL=true` is explicitly configured.
- Provider diagnostics now expose whether the Vercel Solapi override is enabled.
- Deployment documentation now includes explicit Render and Vercel checklists and a clear separation between UI hosting and carrier-delivery hosting.

## Automated Verification

- `DATABASE_URL=sqlite:///:memory: PYTHONPATH=development pytest development/test/unit/web/message/backend/test_provider_status.py development/test/unit/messaging/test_messaging_flows.py development/test/unit/web/message/backend/test_message_template_limits.py development/test/unit/web/message/backend/test_message_send_limits.py -q`
- Result: `18 passed`

## Notes

- This phase did not perform manual testing.
- The Solapi-on-Vercel override exists only as an emergency escape hatch after fixed outbound IP support is intentionally configured.
