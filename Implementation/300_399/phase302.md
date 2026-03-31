## Phase 302

- Increased the default mid-sized AI Agent window footprint so the centered panel is usable without maximize.
- Replaced the old Send Message workspace handoff with an AI Agent-native composer card.
- Added a dedicated messaging JSON endpoint for AI Agent compose data:
  - default recipients
  - AI recommended recipients
  - message templates
- Removed the mobile preview from the AI Agent send flow to keep the composer readable inside the chat window.
- Kept template-based send handoff inside AI Agent by routing `Use In Send Message` into the new composer with the selected template preloaded.
