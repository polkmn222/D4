# Phase 208 Walkthrough

AI Agent chat messages were automatically scrolling the panel after every render. That behavior could override the intended visibility of the workspace/form panel and keep focus on the explanatory message instead.

The automatic scroll behavior has been removed from `appendChatMessage()`, so the UI no longer forcibly shifts focus after each message render.
