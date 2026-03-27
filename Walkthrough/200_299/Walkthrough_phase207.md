# Phase 207 Walkthrough

The AI Agent workspace was a fixed DOM node inside `#ai-agent-body`, while new chat messages were always appended after it. On `OPEN_FORM`, the agent first appended the explanatory message and then opened the workspace, but the workspace stayed above that new message in DOM order.

That made the user see only the message near the bottom while the actual form panel sat higher up in the scroll area.

The workspace is now re-appended to the end of `#ai-agent-body` every time it opens, so create/edit forms and record tabs appear in the expected visible position.
