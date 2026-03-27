from typing import Any, Callable, Dict, Optional

from ai_agent.llm.backend.conversation_context import ConversationContextStore


def build_lead_edit_form_response(
    record_id: str,
    lead_name: str,
    language_preference: Optional[str],
) -> Dict[str, Any]:
    is_korean = (language_preference or "").lower() == "kor"
    return {
        "intent": "OPEN_FORM",
        "object_type": "lead",
        "record_id": record_id,
        "form_url": f"/leads/new-modal?id={record_id}",
        "form_title": f"Edit {lead_name}",
        "form_kind": "lead_edit",
        "text": (
            f"리드 **{lead_name}** 수정 폼을 여기 대화창에 띄웠어요. 바로 수정하고 저장해 주세요."
            if is_korean else
            f"I opened the edit form for **{lead_name}** here in chat. Update the fields you want, then save it."
        ),
        "score": 1.0,
    }


def build_lead_open_record_response(
    *,
    db: Any,
    lead: Any,
    conversation_id: Optional[str],
    action: str,
    language_preference: Optional[str],
    build_chat_card: Callable[[Any, Any, str], Dict[str, Any]],
    lead_name_getter: Callable[[Any], str],
) -> Dict[str, Any]:
    lead_id = str(getattr(lead, "id", ""))
    lead_name = lead_name_getter(lead) if lead else ""
    is_korean = (language_preference or "").lower() == "kor"

    if action == "create":
        text = (
            f"리드 **{lead_name}**이(가) 생성되었습니다! 🎉\n아래에서 상세 내용을 바로 확인하세요. 수정이나 메시지 전송이 필요하면 바로 말씀해 주세요."
            if is_korean else
            f"Lead **{lead_name}** has been created! 🎉\nThe record is now open below. Tell me if you'd like to update a field, send a message, or do anything else."
        )
        if conversation_id:
            ConversationContextStore.clear_pending_create(conversation_id)
            ConversationContextStore.remember_created(conversation_id, "lead", lead_id)
            ConversationContextStore.remember_object(conversation_id, "lead", "CREATE", record_id=lead_id)
    elif action == "update":
        text = (
            f"리드 **{lead_name}** 정보가 업데이트되었습니다! ✅\n최신 상세 내용이 아래에 열려 있어요. 추가로 수정할 내용이 있으면 바로 말씀해 주세요."
            if is_korean else
            f"Lead **{lead_name}** has been updated! ✅\nThe refreshed record is open below. Let me know if you need any other changes."
        )
        if conversation_id:
            ConversationContextStore.remember_object(conversation_id, "lead", "UPDATE", record_id=lead_id)
    else:
        text = (
            f"리드 **{lead_name}** 상세 정보가 아래에 열려 있어요. 수정, 메시지 전송, 또는 다른 작업이 필요하면 바로 말씀해 주세요."
            if is_korean else
            f"Lead **{lead_name}** is now open. You can update any field, send a message, or take any action — just tell me what you need."
        )
        if conversation_id:
            ConversationContextStore.remember_object(conversation_id, "lead", "MANAGE", record_id=lead_id)

    return {
        "intent": "OPEN_RECORD",
        "object_type": "lead",
        "record_id": lead_id,
        "redirect_url": f"/leads/{lead_id}",
        "chat_card": build_chat_card(db, lead, mode="view"),
        "text": text,
    }
