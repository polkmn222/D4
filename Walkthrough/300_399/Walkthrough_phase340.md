# Phase 340 Walkthrough

## Documentation Update

The active runtime docs now describe the narrow message-policy retrieval path, its Qdrant/OpenAI requirements, and the explicit-sync design for Vercel-style deployment.

## Runtime Configuration Check

Checked through the live Python service readers with `PYTHONPATH=development`:

- `OPENAI_API_KEY`: missing
- `QDRANT_ENDPOINT`: set
- `QDRANT_API_KEY`: set
- `QDRANT_MESSAGE_POLICY_COLLECTION`: `message-sending-rules`

## Explicit Sync Attempt

Executed:

```bash
PYTHONPATH=development python <<'PY'
import asyncio
from ai_agent.llm.backend.message_policy_retrieval import MessagePolicyRetrievalService

asyncio.run(MessagePolicyRetrievalService.sync_source_documents())
PY
```

Observed result:

- `ValueError: OPENAI_API_KEY is not set.`

## Outcome

The policy collection was not populated in this phase because the embeddings step cannot run without `OPENAI_API_KEY`.

## Next Required Action

Set `OPENAI_API_KEY` in the active runtime environment, then rerun the explicit sync path.
