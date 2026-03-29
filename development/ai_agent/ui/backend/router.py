from fastapi import APIRouter, Depends, File, Form, Request, UploadFile
from sqlalchemy.orm import Session
from typing import Dict, Any
from db.database import get_db
from ai_agent.debug import debug_event
from ai_agent.ui.backend.service import AiAgentService
from ai_agent.llm.backend.conversation_context import ConversationContextStore
from web.backend.app.utils.error_handler import handle_agent_errors

router = APIRouter(prefix="/api", tags=["AI Agent"])

@router.post("/chat")
@handle_agent_errors
async def chat_with_agent(request: Request, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Endpoint for natural language chat with the AI Agent.
    """
    try:
        body = await request.json()
        query = body.get("query")
        conversation_id = body.get("conversation_id")
        selection = body.get("selection")
        language_preference = body.get("language_preference")
        debug_event(
            "router.chat.request",
            conversation_id=conversation_id,
            query=query,
            has_selection=bool(selection),
            language_preference=language_preference,
        )
        
        if not query:
            return {"intent": "CHAT", "text": "Please provide a query."}
        
        page = body.get("page") or 1
        per_page = body.get("per_page") or 50

        response = await AiAgentService.process_query(
            db,
            query,
            conversation_id=conversation_id,
            page=page,
            per_page=per_page,
            selection=selection,
            language_preference=language_preference,
        )
        debug_event(
            "router.chat.response",
            conversation_id=conversation_id,
            intent=response.get("intent"),
            object_type=response.get("object_type"),
            record_id=response.get("record_id"),
        )
        return response
    except Exception as e:
        return {"intent": "CHAT", "text": f"Error: {str(e)}"}


@router.post("/form-submit")
@handle_agent_errors
async def submit_chat_form(request: Request, db: Session = Depends(get_db)) -> Dict[str, Any]:
    try:
        body = await request.json()
        debug_event(
            "router.form_submit.request",
            conversation_id=body.get("conversation_id"),
            object_type=body.get("object_type"),
            mode=body.get("mode"),
            record_id=body.get("record_id"),
            field_names=sorted((body.get("values") or {}).keys()),
        )
        response = await AiAgentService.submit_chat_native_form(
            db,
            object_type=body.get("object_type"),
            mode=body.get("mode"),
            record_id=body.get("record_id"),
            values=body.get("values") or {},
            conversation_id=body.get("conversation_id"),
            language_preference=body.get("language_preference"),
        )
        debug_event(
            "router.form_submit.response",
            conversation_id=body.get("conversation_id"),
            intent=response.get("intent"),
            object_type=response.get("object_type"),
            record_id=response.get("record_id"),
        )
        return response
    except Exception as e:
        return {"intent": "CHAT", "text": f"Error: {str(e)}"}


@router.post("/reset")
@handle_agent_errors
async def reset_agent_session(request: Request) -> Dict[str, Any]:
    body = await request.json()
    conversation_id = body.get("conversation_id")
    ConversationContextStore.clear(conversation_id)
    debug_event("router.reset", conversation_id=conversation_id)
    return {"status": "ok", "conversation_id": conversation_id}


@router.post("/stt")
@handle_agent_errors
async def transcribe_audio(
    audio: UploadFile = File(...),
    conversation_id: str | None = Form(None),
    language_preference: str | None = Form(None),
) -> Dict[str, Any]:
    debug_event(
        "router.stt.request",
        conversation_id=conversation_id,
        filename=audio.filename,
        content_type=audio.content_type,
        language_preference=language_preference,
    )
    file_bytes = await audio.read()
    response = await AiAgentService.transcribe_audio_bytes(
        file_bytes=file_bytes,
        filename=audio.filename or "ai-agent-voice.webm",
        content_type=audio.content_type or "application/octet-stream",
        language_preference=language_preference,
    )
    debug_event(
        "router.stt.response",
        conversation_id=conversation_id,
        status=response.get("status"),
        provider=response.get("provider"),
        validator=response.get("validator"),
        text_length=len(response.get("text") or ""),
    )
    return response
