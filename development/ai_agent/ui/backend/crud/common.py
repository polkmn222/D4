from typing import Any, Dict, Optional

from ai_agent.llm.backend.conversation_context import ConversationContextStore


def build_object_edit_form_response(
    *,
    object_type: str,
    record_id: str,
    form_url: str,
    title: str,
    language_preference: Optional[str],
) -> Dict[str, Any]:
    is_korean = (language_preference or "").lower() == "kor"
    object_label = object_type.replace("_", " ")
    return {
        "intent": "OPEN_FORM",
        "object_type": object_type,
        "record_id": record_id,
        "form_url": form_url,
        "form_title": title,
        "form_kind": f"{object_type}_edit",
        "text": (
            f"{object_label.title()} **{title.replace('Edit ', '')}** edit form is open in chat."
            if not is_korean else
            f"{object_label.title()} 수정 폼을 대화 안에 열었습니다."
        ),
        "score": 1.0,
    }


def build_object_open_record_response(
    *,
    object_type: str,
    record_id: str,
    redirect_url: str,
    title: str,
    action: str,
    conversation_id: Optional[str],
    language_preference: Optional[str],
    chat_card: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    is_korean = (language_preference or "").lower() == "kor"
    object_label = object_type.replace("_", " ")

    if action == "create":
        text = (
            f"{object_label.title()} **{title}** has been created. The record is open below."
            if not is_korean else
            f"{object_label.title()} **{title}** 레코드가 생성되었고 아래에 열려 있습니다."
        )
        if conversation_id:
            ConversationContextStore.remember_created(conversation_id, object_type, record_id)
            ConversationContextStore.remember_object(conversation_id, object_type, "CREATE", record_id=record_id)
    elif action == "update":
        text = (
            f"{object_label.title()} **{title}** has been updated. The refreshed record is open below."
            if not is_korean else
            f"{object_label.title()} **{title}** 레코드가 업데이트되었고 최신 정보가 아래에 열려 있습니다."
        )
        if conversation_id:
            ConversationContextStore.remember_object(conversation_id, object_type, "UPDATE", record_id=record_id)
    else:
        text = (
            f"{object_label.title()} **{title}** is now open."
            if not is_korean else
            f"{object_label.title()} **{title}** 레코드가 열려 있습니다."
        )
        if conversation_id:
            ConversationContextStore.remember_object(conversation_id, object_type, "MANAGE", record_id=record_id)

    response = {
        "intent": "OPEN_RECORD",
        "object_type": object_type,
        "record_id": record_id,
        "redirect_url": redirect_url,
        "text": text,
    }
    if chat_card:
        response["chat_card"] = chat_card
    return response
