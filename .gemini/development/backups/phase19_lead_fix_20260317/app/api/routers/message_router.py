from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from ...database import get_db
from ...services.message_service import MessageService
from ...services.message_template_service import MessageTemplateService
from ...services.contact_service import ContactService
from ...services.account_service import AccountService
from ...core.templates import templates
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

# --- MESSAGES ---
@router.get("/messages")
async def list_messages(request: Request, db: Session = Depends(get_db)):
    msgs = MessageService.get_messages(db)
    items = []
    for m in msgs:
        contact = ContactService.get_contact(db, m.contact_id) if m.contact_id else None
        items.append({
            "id": m.id,
            "name": m.content[:50] + "..." if m.content and len(m.content) > 50 else m.content,
            "direction": m.direction,
            "status": m.status,
            "contact": f"{contact.first_name} {contact.last_name}" if contact else "",
            "edit_url": f"/messages/new-modal?id={m.id}"
        })
    columns = ["name", "direction", "status", "contact"]
    return templates.TemplateResponse("list_view.html", {
        "request": request, "object_type": "Message", "plural_type": "messages",
        "items": items, "columns": columns
    })

@router.get("/messages/{message_id}")
async def message_detail(request: Request, message_id: str, db: Session = Depends(get_db)):
    try:
        msg = MessageService.get_message(db, message_id)
        if not msg: return RedirectResponse(url="/messages?error=Message+not+found")
        contact = ContactService.get_contact(db, msg.contact_id) if msg.contact_id else None
        
        # Safe account access
        acc = None
        if hasattr(msg, 'account_id') and msg.account_id:
            acc = AccountService.get_account(db, msg.account_id)

        details = {
            "Direction": msg.direction,
            "Status": msg.status,
            "Contact": f"{contact.first_name} {contact.last_name}" if contact else "N/A",
            "Contact_Hidden_Ref": msg.contact_id,
            "Account": acc.name if acc else "N/A",
            "Account_Hidden_Ref": getattr(msg, 'account_id', None),
            "Content": msg.content
        }
        return templates.TemplateResponse("detail_view.html", {
            "request": request, "object_type": "Message", "plural_type": "messages",
            "record_id": message_id, "record_name": "Message Detail", "details": details,
            "created_at": msg.created_at, "updated_at": msg.updated_at, "related_lists": []
        })
    except Exception as e:
        logger.error(f"Error loading message detail: {e}")
        return RedirectResponse(url=f"/messages?error=Error+loading+message+detail")

@router.post("/messages")
async def create_message_route(
    contact_id: str = Form(None),
    account_id: str = Form(None),
    template_id: str = Form(None),
    content: str = Form(...),
    direction: str = Form("Outbound"),
    status: str = Form("Sent"),
    db: Session = Depends(get_db)
):
    msg = MessageService.create_message(
        db, contact_id=contact_id, account_id=account_id, 
        template_id=template_id, content=content, 
        direction=direction, status=status
    )
    return RedirectResponse(url=f"/messages/{msg.id}?success=Record+created+successfully", status_code=303)

@router.post("/messages/{message_id}")
async def update_message_route(
    message_id: str,
    contact_id: str = Form(None),
    account_id: str = Form(None),
    template_id: str = Form(None),
    content: str = Form(...),
    direction: str = Form("Outbound"),
    status: str = Form("Sent"),
    db: Session = Depends(get_db)
):
    MessageService.update_message(
        db, message_id, contact_id=contact_id, account_id=account_id, 
        template_id=template_id, content=content, 
        direction=direction, status=status
    )
    return RedirectResponse(url=f"/messages/{message_id}?success=Record+updated+successfully", status_code=303)

@router.post("/messages/{message_id}/delete")
async def delete_message_route(request: Request, message_id: str, db: Session = Depends(get_db)):
    MessageService.delete_message(db, message_id)
    if "application/json" in request.headers.get("Accept", ""):
        return {"status": "success", "message": "Record deleted successfully"}
    return RedirectResponse(url="/messages?success=Record+deleted+successfully", status_code=303)

# --- MESSAGE TEMPLATES ---
@router.get("/message_templates/new-modal")
async def new_template_modal_base(request: Request, id: str = None, db: Session = Depends(get_db)):
    # This just redirects to the form_router equivalent if needed, 
    # but since list_view.html calls it, we should have it or fix list_view.
    return RedirectResponse(url=f"/message_templates/new?id={id}" if id else "/message_templates/new")

@router.get("/message_templates")
async def list_templates(request: Request, db: Session = Depends(get_db)):
    templates_data = MessageTemplateService.get_templates(db)
    items = []
    for t in templates_data:
        items.append({
            "id": t.id,
            "name": t.name,
            "subject": t.subject,
            "type": t.record_type if hasattr(t, 'record_type') else "SMS",
            "edit_url": f"/message_templates/new-modal?id={t.id}"
        })
    columns = ["name", "subject", "type"]
    return templates.TemplateResponse("list_view.html", {
        "request": request, "object_type": "MessageTemplate", "plural_type": "message_templates",
        "items": items, "columns": columns
    })

@router.get("/message_templates/{template_id}")
async def template_detail(request: Request, template_id: str, db: Session = Depends(get_db)):
    t = MessageTemplateService.get_template(db, template_id)
    if not t: return RedirectResponse(url="/message_templates?error=Template+not+found")
    details = {
        "Name": t.name,
        "Type": t.record_type,
        "Subject": t.subject,
        "Body": t.body
    }
    return templates.TemplateResponse("detail_view.html", {
        "request": request, "object_type": "MessageTemplate", "plural_type": "message_templates",
        "record_id": template_id, "record_name": t.name, "details": details,
        "created_at": t.created_at, "updated_at": t.updated_at, "related_lists": []
    })

@router.post("/message_templates")
async def create_template_route(
    name: str = Form(...),
    subject: str = Form(...),
    body: str = Form(...),
    record_type: str = Form("SMS"),
    db: Session = Depends(get_db)
):
    t = MessageTemplateService.create_template(db, name=name, subject=subject, body=body, record_type=record_type)
    return RedirectResponse(url=f"/message_templates/{t.id}?success=Record+created+successfully", status_code=303)

@router.post("/message_templates/{template_id}")
async def update_template_route(
    template_id: str,
    name: str = Form(...),
    subject: str = Form(...),
    body: str = Form(...),
    record_type: str = Form("SMS"),
    db: Session = Depends(get_db)
):
    MessageTemplateService.update_template(db, template_id, name=name, subject=subject, body=body, record_type=record_type)
    return RedirectResponse(url=f"/message_templates/{template_id}?success=Record+updated+successfully", status_code=303)

@router.post("/message_templates/{template_id}/delete")
async def delete_template_route(request: Request, template_id: str, db: Session = Depends(get_db)):
    MessageTemplateService.delete_template(db, template_id)
    if "application/json" in request.headers.get("Accept", ""):
        return {"status": "success", "message": "Record deleted successfully"}
    return RedirectResponse(url="/message_templates?success=Record+deleted+successfully", status_code=303)
