from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from ...database import get_db
from ...services.contact_service import ContactService
from ...services.asset_service import AssetService
from ...core.templates import templates
from ...core.enums import Gender
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/contacts/{contact_id}")
async def contact_detail(request: Request, contact_id: str, db: Session = Depends(get_db)):
    try:
        logger.info(f"Accessing Contact Detail: {contact_id}")
        contact = ContactService.get_contact(db, contact_id)
        if not contact:
            return RedirectResponse(url="/contacts?error=Contact+not+found")
        
        details = {
            "First Name": contact.first_name if contact.first_name else "",
            "Last Name": contact.last_name if contact.last_name else "",
            "Full Name": f"{contact.first_name if contact.first_name else ''} {contact.last_name if contact.last_name else ''}".strip() or contact.name or "",
            "Email": contact.email if contact.email else "",
            "Phone": contact.phone if contact.phone else "",
            "Website": contact.website if contact.website else "",
            "Tier": contact.tier if contact.tier else "",
            "Created Date": contact.created_at.strftime("%Y-%m-%d %H:%M") if contact.created_at else ""
        }
        
        # Related Assets
        assets = AssetService.get_assets(db, contact=contact_id)
        related_lists = []
        if assets:
            related_lists.append({
                "title": "Assets",
                "columns": ["name", "vin", "status"],
                "items": [{"name": a.name, "vin": a.vin, "status": a.status} for a in assets]
            })

        return templates.TemplateResponse("contacts/detail_view.html", {
            "request": request, "object_type": "Contact", "plural_type": "contacts",
            "record_id": contact_id, "record_name": f"{contact.first_name if contact.first_name else ''} {contact.last_name if contact.last_name else ''}",
            "details": details, "created_at": contact.created_at,
            "updated_at": contact.updated_at, "related_lists": related_lists
        })
    except Exception as e:
        logger.error(f"Error loading contact detail: {e}")
        return RedirectResponse(url=f"/contacts?error=Error+loading+contact+detail:+{str(e).replace(' ', '+')}")

@router.get("/contacts")
async def list_contacts(request: Request, db: Session = Depends(get_db)):
    try:
        contacts = ContactService.get_contacts(db)
        items = []
        for c in contacts:
            items.append({
                "id": c.id,
                "name": f"{c.first_name} {c.last_name}",
                "email": c.email,
                "phone": c.phone,
                "created": c.created_at.strftime("%Y-%m-%d") if c.created_at else "",
                "edit_url": f"/contacts/new?id={c.id}"
            })
        columns = ["name", "email", "phone", "created"]
        return templates.TemplateResponse("contacts/list_view.html", {
            "request": request, 
            "object_type": "Contact", 
            "plural_type": "contacts",
            "items": items, 
            "columns": columns
        })
    except Exception as e:
        logger.error(f"List contacts error: {e}")
        return RedirectResponse(url="/?error=Error+loading+contacts")

@router.post("/contacts")
async def create_contact(
    first_name: str = Form(...),
    last_name: str = Form(...),
    gender: str = Form(None),
    email: str = Form(None),
    phone: str = Form(None),
    website: str = Form(None),
    tier: str = Form(None),
    description: str = Form(None),
    db: Session = Depends(get_db)
):
    contact = ContactService.create_contact(
        db, first_name=first_name, last_name=last_name, gender=gender,
        email=email, phone=phone, website=website,
        tier=tier, description=description
    )
    return RedirectResponse(url=f"/contacts/{contact.id}?success=Record+created+successfully", status_code=303)

@router.post("/contacts/{contact_id}")
async def update_contact(
    contact_id: str,
    first_name: str = Form(...),
    last_name: str = Form(...),
    gender: str = Form(None),
    email: str = Form(None),
    phone: str = Form(None),
    website: str = Form(None),
    tier: str = Form(None),
    description: str = Form(None),
    db: Session = Depends(get_db)
):
    ContactService.update_contact(
        db, contact_id, first_name=first_name, last_name=last_name, 
        gender=gender, email=email, phone=phone,
        website=website, tier=tier, description=description
    )
    return RedirectResponse(url=f"/contacts/{contact_id}" + "?success=Record+updated+successfully", status_code=303)

@router.post("/contacts/{contact_id}/delete")
async def delete_contact(request: Request, contact_id: str, db: Session = Depends(get_db)):
    ContactService.delete_contact(db, contact_id)
    if request.headers.get("Accept") == "application/json":
        return {"status": "success", "message": "Record deleted"}
    return RedirectResponse(url="/contacts?success=Deleted", status_code=303)

@router.post("/contacts/{contact_id}/restore")
async def restore_contact_endpoint(contact_id: str, db: Session = Depends(get_db)):
    contact = ContactService.restore_contact(db, contact_id)
    if contact:
        return {"status": "success"}
    return {"status": "error", "message": "Contact not found"}
