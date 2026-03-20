from fastapi import APIRouter, Request, Depends, Form
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
import os

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/")
async def dashboard(db: Session = Depends(get_db)):
    contacts = ContactService.get_contacts(db)
    return templates.TemplateResponse("dashboard.html", {"request": {}, "contacts": contacts})

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

@router.get("/leads/new")
async def new_lead_form():
    fields = ["first_name", "last_name", "company", "email", "phone", "description"]
    return templates.TemplateResponse("object_form.html", {
        "request": {},
        "object_type": "Lead",
        "contacts": [],
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
async def convert_lead(lead_id: int, db: Session = Depends(get_db)):
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
            "type": "Person Account" if a.is_person_account else "Corporate",
            "industry": a.industry or "Automotive",
            "tier": a.tier
        })
    columns = ["name", "type", "industry", "tier"]
    return templates.TemplateResponse("list_view.html", {
        "request": {}, 
        "object_type": "Account", 
        "items": items, 
        "columns": columns
    })

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

@router.get("/contacts/new")
async def new_contact_form():
    fields = ["first_name", "last_name", "email", "phone", "description"]
    return templates.TemplateResponse("object_form.html", {
        "request": {},
        "object_type": "Contact",
        "contacts": [],
        "fields": fields
    })

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

@router.get("/products/new")
async def new_product_form():
    fields = ["name", "brand", "category", "base_price", "description"]
    return templates.TemplateResponse("object_form.html", {
        "request": {},
        "object_type": "Product",
        "contacts": [],
        "fields": fields
    })

@router.post("/products")
async def create_product(
    name: str = Form(...),
    brand: str = Form("Hyundai"),
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

@router.get("/opportunities/new")
async def new_opportunity_form(db: Session = Depends(get_db)):
    accounts = AccountService.get_accounts(db)
    fields = ["account_id", "name", "amount", "stage", "probability"]
    return templates.TemplateResponse("object_form.html", {
        "request": {},
        "object_type": "Opportunity",
        "contacts": accounts, # Reusing contacts list for account selection
        "fields": fields
    })

@router.post("/opportunities")
async def create_opportunity(
    account_id: int = Form(...),
    name: str = Form(...),
    amount: int = Form(0),
    stage: str = Form("Prospecting"),
    probability: int = Form(10),
    db: Session = Depends(get_db)
):
    OpportunityService.create_opportunity(
        db, account_id=account_id, name=name, amount=amount, stage=stage, probability=probability
    )
    return RedirectResponse(url="/opportunities", status_code=303)

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

@router.get("/assets/new")
async def new_asset_form(db: Session = Depends(get_db)):
    contacts = ContactService.get_contacts(db)
    prods = ProductService.get_products(db)
    fields = ["contact_id", "product_id", "name", "vin", "price"]
    return templates.TemplateResponse("object_form.html", {
        "request": {},
        "object_type": "Asset",
        "contacts": contacts,
        "products": prods,
        "fields": fields
    })

@router.post("/assets")
async def create_asset(
    contact_id: int = Form(...),
    product_id: int = Form(None),
    name: str = Form(...),
    vin: str = Form(None),
    price: int = Form(0),
    db: Session = Depends(get_db)
):
    AssetService.create_asset(
        db, contact_id=contact_id, product_id=product_id, name=name, vin=vin, price=price
    )
    return RedirectResponse(url="/assets", status_code=303)

@router.post("/seed")
async def seed_data(theme: str = Form(...), db: Session = Depends(get_db)):
    from ..services.seed_service import SeedService
    await SeedService.generate_theme_data(db, theme, count=5)
    return RedirectResponse(url="/", status_code=303)
