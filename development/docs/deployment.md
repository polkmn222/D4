# Deployment

## Overview

The active project supports two deployment paths that both resolve to the same FastAPI application.

## Vercel

- Configuration lives in `vercel.json` at the repository root.
- All routes are sent to `api/index.py`.
- `api/index.py` adds `development` to `sys.path` and imports `web.backend.app.main:app`.
- This path keeps Vercel focused on a thin adapter while the real application remains inside `development`.

## Render

- Configuration lives in `render.yaml` at the repository root.
- The web service runs with `rootDir: development`.
- Dependencies are installed with `pip install -r ../requirements.txt`.
- The service starts with `uvicorn web.backend.app.main:app --host 0.0.0.0 --port $PORT`.
- The configured health check path is `/docs`.

## Shared Runtime Behavior

- The main application mounts shared static assets at `/static`.
- Messaging-specific templates are loaded from `web/message/frontend/templates/` through the shared Jinja configuration.
- The AI sub-application is mounted at `/ai-agent`.
- The AI sub-application serves its own assets at `/ai-agent/static` and exposes `/ai-agent/health`.
- Both deployment paths ultimately use the same `web.backend.app.main:app` process tree.

## Recommended Production Delivery Shape

- Keep UI hosting flexible, but centralize protected message delivery on a runtime you control.
- Treat Vercel as a good UI/runtime host, not the preferred direct carrier egress host.
- If local must send directly and Vercel must also send, use a direct provider locally and `MESSAGE_PROVIDER=relay` on Vercel.
- Use Render as the protected relay target when Vercel should hand delivery off to a second runtime.
- Keep Slack as an opt-in dev/test provider only. It is not part of the real carrier delivery chain.
- Use `/messaging/provider-status` to inspect the active provider mode and deployment warnings at runtime.

## Required Environment Variables

### Mandatory

- `DATABASE_URL`: required by `db/database.py`; PostgreSQL is mandatory for the active runtime.
- `OPENAI_API_KEY`: required for the message-policy embedding and retrieval path.
- `QDRANT_ENDPOINT`: required for the message-policy vector collection.
- `QDRANT_API_KEY`: required for authenticated Qdrant access.

### Messaging

- `MESSAGE_PROVIDER`: `mock` by default, `slack` for dev/test notifications, `surem` for direct carrier delivery, `relay` for forwarding delivery to another protected runtime.
- `SLACK_MESSAGE_WEBHOOK_URL`: required only when `MESSAGE_PROVIDER=slack`.
- `RELAY_MESSAGE_ENDPOINT`: required when `MESSAGE_PROVIDER=relay`; points to the protected relay runtime endpoint, typically `https://<render-service>/messaging/relay-dispatch`.
- `RELAY_MESSAGE_TOKEN`: shared bearer secret for relay runtime authentication.
- `RELAY_TARGET_PROVIDER`: provider used by the relay runtime after the handoff. Default is `surem`.
- `APP_BASE_URL`: optional fallback used to build absolute image URLs when uploads remain local.
- `CLOUDINARY_CLOUD_NAME`: enables Cloudinary-backed public MMS image hosting when set.
- `CLOUDINARY_API_KEY` and `CLOUDINARY_API_SECRET`: recommended signed Cloudinary upload/delete credentials.
- `CLOUDINARY_UNSIGNED_UPLOAD_PRESET`: optional upload-only alternative when signed credentials are not available.
- `SUREM_USER_CODE` and `SUREM_SECRET_KEY`: required when `MESSAGE_PROVIDER=surem` or `RELAY_TARGET_PROVIDER=surem`.
- `SUREM_REQ_PHONE`: required SureM request phone for relay-safe sends.
- `SUREM_FORCE_TO_NUMBER`: required fixed-recipient number for the current SureM runtime path.
- `SUREM_AUTH_URL`, `SUREM_SMS_URL`, `SUREM_MMS_URL`, `SUREM_IMAGE_URL`: optional SureM endpoint overrides.
- `QDRANT_MESSAGE_POLICY_COLLECTION`: optional override for the message-policy collection name. Defaults to `message-sending-rules`.

### AI Policy Retrieval

- The AI Agent message-policy retrieval path uses explicit sync rather than startup indexing.
- Run `MessagePolicyRetrievalService.sync_source_documents()` when the policy JSON changes or when a new environment needs the collection populated.
- This design is preferred for Vercel because it avoids hidden writes during cold start and keeps indexing under operator control.

#### Slack Dev/Test Setup

1. Create a Slack Incoming Webhook for a private dev/test channel.
2. Set `MESSAGE_PROVIDER=slack`.
3. Set `SLACK_MESSAGE_WEBHOOK_URL` to the webhook URL.
4. Prefer Cloudinary env vars for public MMS image URLs.
5. If using local uploads instead, set `APP_BASE_URL` to a public hostname or tunnel URL.
6. Run the normal Send Message flow; SMS/LMS/MMS are delivered as Slack-formatted dev/test notifications instead of carrier messages.

#### SureM Carrier Setup

1. Create SureM API credentials.
2. Set `MESSAGE_PROVIDER=surem`.
3. Set `SUREM_USER_CODE`, `SUREM_SECRET_KEY`, `SUREM_REQ_PHONE`, and `SUREM_FORCE_TO_NUMBER`.
4. Keep MMS images as JPG files at or under 500KB.
5. Run the Send Message flow; SMS/LMS/MMS go through SureM and MMS images are uploaded at send time to obtain a provider image key.

#### Vercel and Render Note

- If Vercel stays in front of the app, the simplest structure is still to execute real outbound delivery from a protected relay runtime.
- Render is a suitable relay target because the same application can serve the UI/runtime and accept relay handoff through `/messaging/relay-dispatch`.
- Vercel should prefer `MESSAGE_PROVIDER=relay` when message delivery must be routed through that protected runtime.

## Render Deployment Checklist

1. Create or open the Render web service defined by `render.yaml`.
2. Set `rootDir` to `development` and confirm the start command remains `uvicorn web.backend.app.main:app --host 0.0.0.0 --port $PORT`.
3. Set `DATABASE_URL`.
4. Set `MESSAGE_PROVIDER=surem` if Render should send directly.
5. Set `SUREM_USER_CODE`, `SUREM_SECRET_KEY`, `SUREM_REQ_PHONE`, and `SUREM_FORCE_TO_NUMBER`.
6. Set `APP_BASE_URL` if local upload URLs must be rendered as absolute URLs in non-Cloudinary paths.
7. If Vercel will relay message sends through this runtime, set `RELAY_MESSAGE_TOKEN` here and leave `RELAY_TARGET_PROVIDER=surem`.
8. Deploy once, then call `/messaging/provider-status` and confirm the provider and environment match the intended runtime mode.

### Render Environment Template

Use these values in the Render dashboard for the web service:

```env
DATABASE_URL=<your Neon PostgreSQL URL>
MESSAGE_PROVIDER=surem
RELAY_MESSAGE_TOKEN=<shared secret used by relay callers>
RELAY_TARGET_PROVIDER=surem
SUREM_USER_CODE=<your surem user code>
SUREM_SECRET_KEY=<your surem secret key>
SUREM_REQ_PHONE=<your registered request phone>
SUREM_FORCE_TO_NUMBER=<temporary test number during verification>
APP_BASE_URL=<public Render service URL or custom domain>
CLOUDINARY_CLOUD_NAME=<optional>
CLOUDINARY_API_KEY=<optional>
CLOUDINARY_API_SECRET=<optional>
CLOUDINARY_UNSIGNED_UPLOAD_PRESET=<optional>
```

## Vercel Deployment Checklist

1. Keep Vercel focused on the web entry path through `api/index.py`.
2. Prefer `MESSAGE_PROVIDER=relay` when Vercel needs real send capability.
3. Set `RELAY_MESSAGE_ENDPOINT` to the protected relay runtime endpoint, usually `https://<render-service>/messaging/relay-dispatch`.
4. Set `RELAY_MESSAGE_TOKEN` to the same shared secret configured on the relay runtime.
5. Keep `APP_BASE_URL` set to the public Vercel URL so relative MMS image paths can be converted into public absolute URLs during relay send.
6. After deploy, call `/messaging/provider-status` and confirm the warning set matches the intended environment.

### Vercel Environment Template

For Vercel with real send capability, prefer the relay provider:

```env
DATABASE_URL=<your Neon PostgreSQL URL>
MESSAGE_PROVIDER=relay
RELAY_MESSAGE_ENDPOINT=<your render relay endpoint>
RELAY_MESSAGE_TOKEN=<shared secret>
APP_BASE_URL=<your public Vercel URL>
```

#### MMS Upload Flow

1. `Send Message` image upload stores the file in D4-managed storage first.
2. D4-managed storage is Cloudinary when configured, otherwise local `/static/uploads/...`.
3. This first upload powers draft state, preview, template reuse, and non-direct provider flows.
4. When `MESSAGE_PROVIDER=surem` and the user actually sends an MMS, D4 reads that stored image and uploads it again to SureM to get a provider image key.
5. The final MMS carrier request uses the SureM image key, not the original Cloudinary/local URL.

#### Message Content Rules

1. SMS does not use a subject.
2. Template and compose content can use merge placeholders such as `{Name}` and `{Model}`.
3. SMS content over 90 bytes is upgraded to LMS automatically.
4. LMS and MMS content must be 2000 bytes or fewer.
5. Template and compose upload validation allows JPG images up to 500KB, and the active SureM MMS flow uses that same file-size ceiling.

#### Recommendation

- Do not move the initial `Send Message` upload directly to provider-only storage.
- Keeping the first upload in D4-managed storage gives better overall UX for preview, editing, template persistence, and provider switching.
- Uploading to the carrier provider only at send time avoids premature provider uploads for drafts that are never sent and keeps the UI storage model provider-agnostic.

### AI Providers

- `CELEBRACE_API_KEY`
- `GROQ_API_KEY`

Not every AI provider key is required at once, but provider-specific features depend on the keys being present.

## Verification Checklist

- Confirm `vercel.json` still routes to `api/index.py`.
- Confirm `render.yaml` still starts `web.backend.app.main:app` from `development`.
- Confirm `docs/architecture.md` matches the current mount points and entry paths.
- Confirm `DATABASE_URL` requirements are documented whenever database setup changes.
- Confirm at least one external provider path remains verifiable:
  - `slack` for safe dev/test end-to-end notification checks
  - `surem` for real carrier delivery when the protected runtime is configured
