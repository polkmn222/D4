import json
import logging
import os
from typing import Any


logger = logging.getLogger("ai_agent.debug")


def ai_agent_debug_enabled() -> bool:
    raw = os.getenv("AI_AGENT_DEBUG", "").strip().lower()
    return raw in {"1", "true", "yes", "on", "debug"}


def _normalize(value: Any) -> Any:
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    if isinstance(value, dict):
        return {str(key): _normalize(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_normalize(item) for item in value]
    return str(value)


def debug_event(stage: str, **details: Any) -> None:
    if not ai_agent_debug_enabled():
        return
    payload = {"stage": stage, **{key: _normalize(value) for key, value in details.items()}}
    logger.info("ai_agent_debug %s", json.dumps(payload, ensure_ascii=True, sort_keys=True))
