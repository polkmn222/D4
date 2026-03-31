## Phase 303

- Increased the default AI Agent height again so the in-chat composer has more usable vertical space.
- Split the AI Agent Send Message layout by window state:
  - normal/mid-size: single-column composer without mobile preview
  - maximized: two-column composer with mobile preview
- Added send-time validation in the AI Agent composer so send is blocked with a clear chat message when:
  - no content/template is provided
  - MMS is selected without an image-backed template
- Re-render Send Message composers when maximize/restore changes so the preview appears and disappears immediately.
