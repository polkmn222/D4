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

- Keep UI hosting flexible, but centralize real SMS/LMS/MMS delivery on Render when Solapi IP allowlisting matters.
- Treat Vercel as a good UI/runtime host, not the preferred Solapi egress host, unless Static IPs or Secure Compute is explicitly enabled.
- If local must send directly and Vercel must also send, use `MESSAGE_PROVIDER=solapi` locally and `MESSAGE_PROVIDER=relay` on Vercel so only the relay runtime needs Solapi allowlisting.
- Keep Slack as an opt-in dev/test provider only. It is not part of the real carrier delivery chain.
- Use `/messaging/provider-status` to inspect the active provider mode and deployment warnings at runtime.

## Required Environment Variables

### Mandatory

- `DATABASE_URL`: required by `db/database.py`; PostgreSQL is mandatory for the active runtime.

### Messaging

- `MESSAGE_PROVIDER`: `mock` by default, `slack` for dev/test notifications, `solapi` for real carrier delivery, `relay` for forwarding delivery to another protected runtime.
- `ALLOW_SOLAPI_ON_VERCEL`: optional emergency override. Leave unset by default. Only enable if Vercel outbound IPs are fixed and allowlisted.
- `SLACK_MESSAGE_WEBHOOK_URL`: required only when `MESSAGE_PROVIDER=slack`.
- `RELAY_MESSAGE_ENDPOINT`: required when `MESSAGE_PROVIDER=relay`; points to the protected relay runtime endpoint, typically `https://<render-service>/messaging/relay-dispatch`.
- `RELAY_MESSAGE_TOKEN`: shared bearer secret for relay runtime authentication.
- `RELAY_TARGET_PROVIDER`: provider used by the relay runtime after the handoff. Default is `solapi`.
- `APP_BASE_URL`: optional fallback used to build absolute image URLs when uploads remain local.
- `CLOUDINARY_CLOUD_NAME`: enables Cloudinary-backed public MMS image hosting when set.
- `CLOUDINARY_API_KEY` and `CLOUDINARY_API_SECRET`: recommended signed Cloudinary upload/delete credentials.
- `CLOUDINARY_UNSIGNED_UPLOAD_PRESET`: optional upload-only alternative when signed credentials are not available.
- `SOLAPI_API_KEY` and `SOLAPI_API_SECRET`: required when `MESSAGE_PROVIDER=solapi`.
- `SOLAPI_SENDER_NUMBER`: registered Solapi sender number used for SMS/LMS/MMS dispatch.
- `SOLAPI_ALLOWED_IP`: optional operator note for the allowlisted outbound IP used in the Solapi console.
- `SOLAPI_FORCE_TO_NUMBER`: optional safety override that forces every Solapi send to a single test recipient.

#### Slack Dev/Test Setup

1. Create a Slack Incoming Webhook for a private dev/test channel.
2. Set `MESSAGE_PROVIDER=slack`.
3. Set `SLACK_MESSAGE_WEBHOOK_URL` to the webhook URL.
4. Prefer Cloudinary env vars for public MMS image URLs.
5. If using local uploads instead, set `APP_BASE_URL` to a public hostname or tunnel URL.
6. Run the normal Send Message flow; SMS/LMS/MMS are delivered as Slack-formatted dev/test notifications instead of carrier messages.

#### Solapi Carrier Setup

1. Create Solapi API credentials and allowlist the runtime IP in the Solapi console if the account is IP-restricted.
2. Register and activate at least one sender number in Solapi.
3. Set `MESSAGE_PROVIDER=solapi`.
4. Set `SOLAPI_API_KEY`, `SOLAPI_API_SECRET`, and `SOLAPI_SENDER_NUMBER`.
5. Keep MMS images at 200KB or smaller; Solapi rejects larger MMS uploads.
6. Run the Send Message flow; SMS/LMS go straight to carrier delivery and MMS images are uploaded to Solapi storage before send.
7. If Solapi returns a `Forbidden` response mentioning an IP address, the runtime egress IP is not in the Solapi allowlist yet; carrier send verification is blocked until the allowlist is updated.

#### Vercel and Render Note

- Render is the simpler production target for Solapi because the message-sending runtime can be allowlisted directly.
- Vercel uses dynamic outbound IPs by default. According to Vercel's November 10, 2025 knowledge-base guidance, fixed egress requires Static IPs or Secure Compute.
- If Vercel stays in front of the app, the simplest structure is still to execute actual Solapi sends from the Render runtime.
- The runtime now blocks `MESSAGE_PROVIDER=solapi` on Vercel by default unless `ALLOW_SOLAPI_ON_VERCEL=true` is explicitly set.

## Render Deployment Checklist

1. Create or open the Render web service defined by `render.yaml`.
2. Set `rootDir` to `development` and confirm the start command remains `uvicorn web.backend.app.main:app --host 0.0.0.0 --port $PORT`.
3. Set `DATABASE_URL`.
4. Set `MESSAGE_PROVIDER=solapi`.
5. Set `SOLAPI_API_KEY`, `SOLAPI_API_SECRET`, and `SOLAPI_SENDER_NUMBER`.
6. Set `SOLAPI_FORCE_TO_NUMBER` while verifying production wiring.
7. Set `APP_BASE_URL` if local upload URLs must be rendered as absolute URLs in non-Cloudinary paths.
8. Deploy once, then call `/messaging/provider-status` and confirm the provider is `solapi` and the environment shows Render.
9. Identify the Render outbound IP or outbound IP range from the Render dashboard or docs.
10. Register that Render outbound IP information in the Solapi allowlist.
11. Send one forced-recipient SMS, then one MMS under 200KB, and confirm both are accepted.
12. If Vercel will relay message sends through this runtime, set `RELAY_MESSAGE_TOKEN` here and leave `RELAY_TARGET_PROVIDER=solapi`.

### Render Environment Template

Use these values in the Render dashboard for the web service:

```env
DATABASE_URL=<your Neon PostgreSQL URL>
MESSAGE_PROVIDER=solapi
RELAY_MESSAGE_TOKEN=<shared secret used by relay callers>
RELAY_TARGET_PROVIDER=solapi
SOLAPI_API_KEY=<your solapi api key>
SOLAPI_API_SECRET=<your solapi api secret>
SOLAPI_SENDER_NUMBER=<registered sender number>
SOLAPI_FORCE_TO_NUMBER=<temporary test number during verification>
SOLAPI_ALLOWED_IP=<operator note for the Render outbound IP or range>
APP_BASE_URL=<public Render service URL or custom domain>
CLOUDINARY_CLOUD_NAME=<optional>
CLOUDINARY_API_KEY=<optional>
CLOUDINARY_API_SECRET=<optional>
CLOUDINARY_UNSIGNED_UPLOAD_PRESET=<optional>
```

### Render Allowlist Procedure

1. Deploy the Render service once with the Solapi env vars in place.
2. Open `/messaging/provider-status` and confirm:
   - `provider=solapi`
   - `environment.render=true`
3. In the Render dashboard, locate the service outbound IP or outbound IP range for the active region.
4. Add that Render outbound IP or range to the Solapi API key allowlist.
5. Keep your home and office IPs only for local verification. They do not replace the Render allowlist entry.
6. Re-run one forced-recipient SMS test.
7. Re-run one forced-recipient MMS test with an image under 200KB.

## Vercel Deployment Checklist

1. Keep Vercel focused on the web entry path through `api/index.py`.
2. Do not rely on default Vercel outbound networking for Solapi allowlisting.
3. If Vercel needs real send capability, prefer `MESSAGE_PROVIDER=relay`.
4. Set `RELAY_MESSAGE_ENDPOINT` to the protected relay runtime endpoint, usually `https://<render-service>/messaging/relay-dispatch`.
5. Set `RELAY_MESSAGE_TOKEN` to the same shared secret configured on the relay runtime.
6. Keep `APP_BASE_URL` set to the public Vercel URL so relative MMS image paths can be converted into public absolute URLs during relay send.
7. If Vercel must send through Solapi directly, confirm fixed outbound IP support first, allowlist it in Solapi, and only then set `ALLOW_SOLAPI_ON_VERCEL=true`.
8. After deploy, call `/messaging/provider-status` and confirm the warning set matches the intended environment.

### Vercel Environment Template

For Vercel with real send capability, prefer the relay provider:

```env
DATABASE_URL=<your Neon PostgreSQL URL>
MESSAGE_PROVIDER=relay
RELAY_MESSAGE_ENDPOINT=<your render relay endpoint>
RELAY_MESSAGE_TOKEN=<shared secret>
APP_BASE_URL=<your public Vercel URL>
```

If Vercel must use Solapi directly in the future, that is a separate operating mode and should only be enabled after fixed outbound IP support is confirmed and allowlisted.

#### MMS Upload Flow

1. `Send Message` image upload stores the file in D4-managed storage first.
2. D4-managed storage is Cloudinary when configured, otherwise local `/static/uploads/...`.
3. This first upload powers draft state, preview, template reuse, and non-Solapi provider flows.
4. When `MESSAGE_PROVIDER=solapi` and the user actually sends an MMS, D4 reads that stored image and uploads it again to Solapi storage to get a Solapi `imageId`.
5. The final MMS carrier request uses the Solapi `imageId`, not the original Cloudinary/local URL.

#### Message Content Rules

1. SMS does not use a subject.
2. Template and compose content can use merge placeholders such as `{Name}` and `{Model}`.
3. SMS content over 90 bytes is upgraded to LMS automatically.
4. LMS and MMS content must be 2000 bytes or fewer.
5. Template and compose upload validation allows JPG images up to 500KB, but Solapi carrier upload still enforces its own 200KB MMS image limit.

#### Recommendation

- Do not move the initial `Send Message` upload directly to Solapi-only storage yet.
- Keeping the first upload in D4-managed storage gives better overall UX for preview, editing, template persistence, and provider switching.
- Uploading to Solapi only at send time avoids premature Solapi uploads for drafts that are never sent and keeps the UI storage model provider-agnostic.
- Revisit direct-to-Solapi upload only if the product intentionally becomes Solapi-only and draft/template image reuse is redesigned around Solapi file lifecycle management.

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
  - `solapi` for real carrier delivery after IP allowlist validation
