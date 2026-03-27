from typing import Any, Dict, List, Optional


def build_chat_native_form(
    *,
    form_id: str,
    object_type: str,
    mode: str,
    title: str,
    submit_label: str,
    cancel_label: str,
    required_fields: List[str],
    fields: List[Dict[str, Any]],
    record_id: Optional[str] = None,
    description: Optional[str] = None,
    field_errors: Optional[Dict[str, str]] = None,
    form_error: Optional[str] = None,
) -> Dict[str, Any]:
    form: Dict[str, Any] = {
        "version": "v1",
        "form_id": form_id,
        "object_type": object_type,
        "mode": mode,
        "title": title,
        "submit_label": submit_label,
        "cancel_label": cancel_label,
        "required_fields": required_fields,
        "fields": fields,
        "state": {"status": "ready"},
        "submit": {
            "endpoint": "/ai-agent/api/form-submit",
            "method": "POST",
        },
    }
    if record_id:
        form["record_id"] = record_id
    if description:
        form["description"] = description
    if field_errors:
        form["field_errors"] = field_errors
    if form_error:
        form["form_error"] = form_error
    return form
