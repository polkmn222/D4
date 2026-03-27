from typing import Any, Dict

from fastapi import APIRouter
from pydantic import BaseModel

from agent.ui.backend.service import build_agent_bootstrap_payload, parse_agent_command


router = APIRouter()


class AgentCommandRequest(BaseModel):
    command: str


@router.get("/api/bootstrap")
async def agent_bootstrap() -> Dict[str, Any]:
    return build_agent_bootstrap_payload()


@router.post("/api/command")
async def run_agent_command(payload: AgentCommandRequest) -> Dict[str, Any]:
    return parse_agent_command(payload.command)

