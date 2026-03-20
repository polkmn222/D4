from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from ..database import get_db
from ..services.contact_service import ContactService
from ..services.ai_service import AIService
import os

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/")
async def dashboard(db: Session = Depends(get_db)):
    contacts = ContactService.get_contacts(db)
    return templates.TemplateResponse("dashboard.html", {"request": {}, "contacts": contacts})

# --- CONTACTS ---
@router.get("/contacts")
async def list_contacts(db: Session = Depends(get_db)):
    contacts = ContactService.get_contacts(db)
    # Convert models to dicts for the generic template
    items = []
    for c in contacts:
        items.append({
            "id": c.id,
            "name": f"{c.first_name} {c.last_name}",
            "email": c.email,
            "phone": c.phone,
            "status": c.status
        })
    columns = ["name", "email", "phone", "status"]
    return templates.TemplateResponse("list_view.html", {
        "request": {}, 
        "object_type": "Contact", 
        "items": items, 
        "columns": columns
    })

@router.get("/contacts/new")
async def new_contact_form(request: Request):
    return templates.TemplateResponse("contact_form.html", {"request": request, "contact": None})

@router.post("/contacts/new")
async def create_contact(
    request: Request,
    first_name: str = Form(...),
    last_name: str = Form(...),
    email: str = Form(...),
    phone: str = Form(None),
    lead_source: str = Form("Manual"),
    status: str = Form("New"),
    description: str = Form(None),
    db: Session = Depends(get_db)
):
    # Generate AI Summary if description is provided
    ai_summary = await AIService.generate_summary(description) if description else ""
    
    ContactService.create_contact(
        db, 
        first_name=first_name, 
        last_name=last_name, 
        email=email, 
        phone=phone,
        lead_source=lead_source,
        status=status,
        description=description,
        ai_summary=ai_summary
    )
    return RedirectResponse(url="/", status_code=303)

@router.get("/contacts/{contact_id}/edit")
async def edit_contact_form(request: Request, contact_id: int, db: Session = Depends(get_db)):
    contact = ContactService.get_contact(db, contact_id)
    return templates.TemplateResponse("contact_form.html", {"request": request, "contact": contact})

@router.post("/contacts/{contact_id}/edit")
async def update_contact(
    contact_id: int,
    first_name: str = Form(...),
    last_name: str = Form(...),
    email: str = Form(...),
    phone: str = Form(None),
    lead_source: str = Form("Manual"),
    status: str = Form("New"),
    description: str = Form(None),
    db: Session = Depends(get_db)
):
    # Fetch existing contact to check if description changed
    existing = ContactService.get_contact(db, contact_id)
    ai_summary = existing.ai_summary
    
    # Re-generate summary if description changed or is new
    if description != existing.description:
        ai_summary = await AIService.generate_summary(description) if description else ""

    ContactService.update_contact(
        db, 
        contact_id, 
        first_name=first_name, 
        last_name=last_name, 
        email=email, 
        phone=phone,
        lead_source=lead_source,
        status=status,
        description=description,
        ai_summary=ai_summary
    )
    return RedirectResponse(url="/", status_code=303)

@router.post("/contacts/{contact_id}/delete")
async def delete_contact(contact_id: int, db: Session = Depends(get_db)):
    ContactService.delete_contact(db, contact_id)
    return RedirectResponse(url="/", status_code=303)

@router.post("/seed")
async def seed_data(theme: str = Form(...), db: Session = Depends(get_db)):
    from ..services.seed_service import SeedService
    await SeedService.generate_theme_data(db, theme, count=5)
    return RedirectResponse(url="/", status_code=303)

# --- OPPORTUNITIES ---
@router.get("/opportunities")
async def list_opportunities(db: Session = Depends(get_db)):
    from ..services.opportunity_service import OpportunityService
    opps = OpportunityService.get_opportunities(db)
    items = []
    for o in opps:
        items.append({
            "id": o.id,
            "name": o.name,
            "amount": f"{o.amount:,} KRW",
            "stage": o.stage,
            "probability": f"{o.probability}%"
        })
    columns = ["name", "amount", "stage", "probability"]
    return templates.TemplateResponse("list_view.html", {
        "request": {}, 
        "object_type": "Opportunity", 
        "items": items, 
        "columns": columns
    })

@router.get("/opportunities/new")
async def new_opportunity_form(db: Session = Depends(get_db)):
    contacts = ContactService.get_contacts(db)
    fields = ["contact_id", "name", "amount", "stage", "probability"]
    return templates.TemplateResponse("object_form.html", {
        "request": {},
        "object_type": "Opportunity",
        "contacts": contacts,
        "fields": fields
    })

@router.post("/opportunities")
async def create_opportunity(
    contact_id: int = Form(...),
    name: str = Form(...),
    amount: int = Form(0),
    stage: str = Form("Prospecting"),
    probability: int = Form(10),
    db: Session = Depends(get_db)
):
    from ..services.opportunity_service import OpportunityService
    OpportunityService.create_opportunity(
        db, contact_id=contact_id, name=name, amount=amount, stage=stage, probability=probability
    )
    return RedirectResponse(url="/opportunities", status_code=303)

# --- ASSETS ---
@router.get("/assets")
async def list_assets(db: Session = Depends(get_db)):
    from ..services.asset_service import AssetService
    assets = AssetService.get_assets(db)
    items = []
    for a in assets:
        items.append({
            "id": a.id,
            "name": a.name,
            "status": a.status,
            "price": f"{a.price:,} KRW"
        })
    columns = ["name", "status", "price"]
    return templates.TemplateResponse("list_view.html", {
        "request": {}, 
        "object_type": "Asset", 
        "items": items, 
        "columns": columns
    })

@router.get("/assets/new")
async def new_asset_form(db: Session = Depends(get_db)):
    contacts = ContactService.get_contacts(db)
    fields = ["contact_id", "name", "status", "serial_number", "price"]
    return templates.TemplateResponse("object_form.html", {
        "request": {},
        "object_type": "Asset",
        "contacts": contacts,
        "fields": fields
    })

@router.post("/assets")
async def create_asset(
    contact_id: int = Form(...),
    name: str = Form(...),
    status: str = Form("Active"),
    serial_number: str = Form(None),
    price: int = Form(0),
    db: Session = Depends(get_db)
):
    from ..services.asset_service import AssetService
    AssetService.create_asset(
        db, contact_id=contact_id, name=name, status=status, serial_number=serial_number, price=price
    )
    return RedirectResponse(url="/assets", status_code=303)

# --- PLACEHOLDERS ---
@router.get("/leads")
@router.get("/tasks")
@router.get("/accounts")
async def placeholders():
    return RedirectResponse(url="/")
