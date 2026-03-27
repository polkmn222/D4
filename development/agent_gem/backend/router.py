from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from typing import Dict, Any
from db.database import get_db
from agent_gem.backend.service import AgentGemService
from web.backend.app.utils.error_handler import handle_agent_errors
from web.backend.app.core.templates import templates

router = APIRouter(prefix="/api", tags=["Agent Gem"])

@router.get("/ui", response_class=HTMLResponse)
async def get_agent_ui(request: Request):
    """
    Serve the Agent Gem chat interface.
    """
    return templates.TemplateResponse("agent_gem/index.html", {"request": request})

@router.post("/chat")
@handle_agent_errors
async def chat_with_agent(request: Request, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Endpoint for natural language chat with the Agent Gem.
    """
    try:
        body = await request.json()
        query = body.get("query")
        conversation_id = body.get("conversation_id")
        selection = body.get("selection")
        language_preference = body.get("language_preference")
        
        if not query:
            return {"intent": "CHAT", "text": "Please provide a query."}
        
        page = body.get("page") or 1
        per_page = body.get("per_page") or 50

        response = await AgentGemService.process_query(
            db,
            query,
            conversation_id=conversation_id,
            page=page,
            per_page=per_page,
            selection=selection,
            language_preference=language_preference,
        )
        return response
    except Exception as e:
        return {"intent": "CHAT", "text": f"Error: {str(e)}"}


@router.post("/reset")
@handle_agent_errors
async def reset_agent_session(request: Request) -> Dict[str, Any]:
    # Placeholder for resetting conversation context if needed
    body = await request.json()
    conversation_id = body.get("conversation_id")
    # if ConversationContextStore exist...
    return {"status": "ok", "conversation_id": conversation_id}
