from fastapi import APIRouter, Request, Depends, Form, UploadFile, File
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from ..database import get_db
from ..services.contact_service import ContactService
from ..services.ai_service import AIService
from ..services.lead_service import LeadService
from ..services.account_service import AccountService
from ..services.product_service import ProductService
from ..services.opportunity_service import OpportunityService
from ..services.asset_service import AssetService
from ..services.task_service import TaskService
from ..services.import_service import ImportService
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

@router.get("/contacts/new-modal")
async def new_contact_modal():
    fields = ["first_name", "last_name", "email", "phone", "description"]
    return templates.TemplateResponse("object_form.html", {
        "request": {},
        "object_type": "Contact",
        "fields": fields
    })

@router.post("/contacts")
async def create_contact(
    first_name: str = Form(...),
    last_name: str = Form(...),
    email: str = Form(...),
    phone: str = Form(None),
    description: str = Form(None),
    db: Session = Depends(get_db)
):
    ContactService.create_contact(
        db, first_name=first_name, last_name=last_name, email=email, 
        phone=phone, description=description
    )
    return RedirectResponse(url="/contacts", status_code=303)

# --- LEADS ---
@router.get("/leads")
async def list_leads(db: Session = Depends(get_db)):
    leads = LeadService.get_leads(db, converted=False)
    items = []
    for l in leads:
        items.append({
            "id": l.id,
            "name": f"{l.first_name} {l.last_name}",
            "company": l.company or "Personal",
            "email": l.email,
            "status": l.status
        })
    columns = ["name", "company", "email", "status"]
    return templates.TemplateResponse("list_view.html", {
        "request": {}, 
        "object_type": "Lead", 
        "items": items, 
        "columns": columns
    })

@router.get("/leads/new-modal")
async def new_lead_modal():
    fields = ["first_name", "last_name", "company", "email", "phone", "description"]
    return templates.TemplateResponse("object_form.html", {
        "request": {},
        "object_type": "Lead",
        "fields": fields
    })

@router.post("/leads")
async def create_lead(
    first_name: str = Form(...),
    last_name: str = Form(...),
    company: str = Form(None),
    email: str = Form(...),
    phone: str = Form(None),
    description: str = Form(None),
    db: Session = Depends(get_db)
):
    LeadService.create_lead(
        db, first_name=first_name, last_name=last_name, company=company, 
        email=email, phone=phone, description=description
    )
    return RedirectResponse(url="/leads", status_code=303)

@router.post("/leads/{lead_id}/convert")
async def convert_lead(lead_id: str, db: Session = Depends(get_db)):
    LeadService.convert_lead(db, lead_id)
    return RedirectResponse(url="/opportunities", status_code=303)

# --- ACCOUNTS ---
@router.get("/accounts")
async def list_accounts(db: Session = Depends(get_db)):
    accounts = AccountService.get_accounts(db)
    items = []
    for a in accounts:
        items.append({
            "id": a.id,
            "name": a.name,
            "type": a.record_type,
            "status": a.status,
            "industry": a.industry or "Automotive",
            "tier": a.tier
        })
    columns = ["name", "type", "status", "industry", "tier"]
    return templates.TemplateResponse("list_view.html", {
        "request": {}, 
        "object_type": "Account", 
        "items": items, 
        "columns": columns
    })

@router.get("/accounts/record-types")
async def account_record_type_modal():
    return templates.TemplateResponse("account_record_type.html", {"request": {}})

@router.get("/accounts/new")
async def new_account_modal(type: str = "Individual"):
    fields = ["name", "industry", "website", "status", "description"]
    return templates.TemplateResponse("object_form.html", {
        "request": {},
        "object_type": "Account",
        "record_type": type,
        "fields": fields
    })

@router.post("/accounts")
async def create_account(
    name: str = Form(...),
    record_type: str = Form("Individual"),
    status: str = Form("Active"),
    industry: str = Form(None),
    website: str = Form(None),
    description: str = Form(None),
    db: Session = Depends(get_db)
):
    AccountService.create_account(
        db, name=name, record_type=record_type, status=status,
        industry=industry, website=website, description=description, 
        is_person_account=(record_type=="Individual")
    )
    return RedirectResponse(url="/accounts", status_code=303)

# --- OPPORTUNITIES ---
@router.get("/opportunities")
async def list_opportunities(db: Session = Depends(get_db)):
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

@router.get("/opportunities/new-modal")
async def new_opportunity_modal(db: Session = Depends(get_db)):
    accounts = AccountService.get_accounts(db)
    fields = ["account_id", "name", "amount", "stage", "status", "probability"]
    return templates.TemplateResponse("object_form.html", {
        "request": {},
        "object_type": "Opportunity",
        "accounts": accounts,
        "fields": fields
    })

@router.post("/opportunities")
async def create_opportunity(
    account_id: str = Form(...),
    name: str = Form(...),
    amount: int = Form(0),
    stage: str = Form("Prospecting"),
    status: str = Form("Open"),
    probability: int = Form(10),
    db: Session = Depends(get_db)
):
    OpportunityService.create_opportunity(
        db, account_id=account_id, name=name, amount=amount, 
        stage=stage, status=status, probability=probability
    )
    return RedirectResponse(url="/opportunities", status_code=303)

# --- PRODUCTS ---
@router.get("/products")
async def list_products(db: Session = Depends(get_db)):
    products = ProductService.get_products(db)
    items = []
    for p in products:
        items.append({
            "id": p.id,
            "name": p.name,
            "brand": p.brand,
            "category": p.category,
            "price": f"{p.base_price:,} KRW"
        })
    columns = ["name", "brand", "category", "price"]
    return templates.TemplateResponse("list_view.html", {
        "request": {}, 
        "object_type": "Product", 
        "items": items, 
        "columns": columns
    })

@router.get("/products/new-modal")
async def new_product_modal():
    fields = ["name", "brand", "category", "base_price", "description"]
    return templates.TemplateResponse("object_form.html", {
        "request": {},
        "object_type": "Product",
        "fields": fields
    })

@router.post("/products")
async def create_product(
    name: str = Form(...),
    brand: str = Form("Solaris"),
    category: str = Form("SUV"),
    base_price: int = Form(0),
    description: str = Form(None),
    db: Session = Depends(get_db)
):
    ProductService.create_product(
        db, name=name, brand=brand, category=category, 
        base_price=base_price, description=description
    )
    return RedirectResponse(url="/products", status_code=303)

# --- ASSETS ---
@router.get("/assets")
async def list_assets(db: Session = Depends(get_db)):
    assets = AssetService.get_assets(db)
    items = []
    for a in assets:
        items.append({
            "id": a.id,
            "name": a.name,
            "vin": a.vin or "N/A",
            "status": a.status,
            "price": f"{a.price:,} KRW"
        })
    columns = ["name", "vin", "status", "price"]
    return templates.TemplateResponse("list_view.html", {
        "request": {}, 
        "object_type": "Asset", 
        "items": items, 
        "columns": columns
    })

@router.get("/assets/new-modal")
async def new_asset_modal(db: Session = Depends(get_db)):
    contacts = ContactService.get_contacts(db)
    fields = ["contact_id", "name", "vin", "price"]
    return templates.TemplateResponse("object_form.html", {
        "request": {},
        "object_type": "Asset",
        "contacts": contacts,
        "fields": fields
    })

@router.post("/assets")
async def create_asset(
    contact_id: str = Form(...),
    name: str = Form(...),
    vin: str = Form(None),
    price: int = Form(0),
    db: Session = Depends(get_db)
):
    AssetService.create_asset(
        db, contact_id=contact_id, name=name, vin=vin, price=price
    )
    return RedirectResponse(url="/assets", status_code=303)

@router.get("/seed") # Re-adding seed as I might have messed it up in previous rewrite
async def seed_page(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})

@router.post("/seed")
async def seed_data(theme: str = Form(...), db: Session = Depends(get_db)):
    from ..services.seed_service import SeedService
    await SeedService.generate_theme_data(db, theme, count=5)
    return RedirectResponse(url="/", status_code=303)

# --- IMPORT ---
@router.get("/import-modal")
async def import_modal(object_type: str):
    return templates.TemplateResponse("import_modal.html", {"request": {}, "object_type": object_type})

@router.post("/import")
async def import_csv(
    object_type: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    content = await file.read()
    decoded = content.decode("utf-8")
    count = await ImportService.import_csv(db, object_type, decoded)
    return RedirectResponse(url=f"/{object_type.lower()}s", status_code=303)
