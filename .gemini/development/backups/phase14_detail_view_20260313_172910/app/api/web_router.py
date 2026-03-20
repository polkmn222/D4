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
from ..services.campaign_service import CampaignService
from ..services.vehicle_spec_service import VehicleSpecService
import os

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/")
async def dashboard(db: Session = Depends(get_db)):
    contacts = ContactService.get_contacts(db)
    return templates.TemplateResponse("dashboard.html", {"request": {}, "contacts": contacts})

# --- CONTACTS ---
@router.get("/contacts/{contact_id}")
async def contact_detail(contact_id: str, db: Session = Depends(get_db)):
    contact = ContactService.get_contact(db, contact_id)
    if not contact:
        return RedirectResponse(url="/contacts")
    
    details = {
        "Name": f"{contact.first_name} {contact.last_name}",
        "Email": contact.email,
        "Phone": contact.phone,
        "Account_Id": contact.account_id,
        "Gender": contact.gender,
        "Created_Date": contact.created_at.strftime("%Y-%m-%d %H:%M") if contact.created_at else "N/A"
    }
    
    # Related Assets
    assets = AssetService.get_assets(db, account_id=contact.account_id)
    related_lists = []
    if assets:
        related_lists.append({
            "title": "Assets",
            "columns": ["name", "vin", "status"],
            "items": [{"name": a.name, "vin": a.vin, "status": a.status} for a in assets]
        })

    return templates.TemplateResponse("detail_view.html", {
        "request": {},
        "object_type": "Contact",
        "record_name": f"{contact.first_name} {contact.last_name}",
        "details": details,
        "related_lists": related_lists
    })
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
async def new_contact_modal(request: Request):
    fields = ["first_name", "last_name", "gender", "email", "phone", "description"]
    return templates.TemplateResponse("object_form.html", {
        "request": request,
        "object_type": "Contact",
        "fields": fields
    })

@router.post("/contacts")
async def create_contact(
    first_name: str = Form(...),
    last_name: str = Form(...),
    gender: str = Form(None),
    email: str = Form(...),
    phone: str = Form(None),
    description: str = Form(None),
    db: Session = Depends(get_db)
):
    ContactService.create_contact(
        db, first_name=first_name, last_name=last_name, gender=gender,
        email=email, phone=phone, description=description
    )
    return RedirectResponse(url="/contacts", status_code=303)

@router.get("/leads/{lead_id}")
async def lead_detail(lead_id: str, db: Session = Depends(get_db)):
    lead = LeadService.get_lead(db, lead_id)
    if not lead:
        return RedirectResponse(url="/leads")
    
    details = {
        "Name": f"{lead.first_name} {lead.last_name}",
        "Status": lead.status,
        "Email": lead.email,
        "Phone": lead.phone,
        "Gender": lead.gender,
        "Created_Date": lead.created_at.strftime("%Y-%m-%d %H:%M") if lead.created_at else "N/A"
    }
    
    # Path/Progress bar
    stages = ["New", "Follow Up", "Qualified", "Lost"]
    path = []
    found_active = False
    for s in stages:
        is_active = (s == lead.status)
        is_completed = not found_active and not is_active
        if is_active: found_active = True
        path.append({"label": s, "active": is_active, "completed": is_completed})

    return templates.TemplateResponse("detail_view.html", {
        "request": {},
        "object_type": "Lead",
        "record_name": f"{lead.first_name} {lead.last_name}",
        "details": details,
        "path": path,
        "related_lists": []
    })
@router.get("/leads")
async def list_leads(db: Session = Depends(get_db)):
    leads = LeadService.get_leads(db, converted=False)
    items = []
    for l in leads:
        items.append({
            "id": l.id,
            "name": f"{l.first_name} {l.last_name}",
            "email": l.email,
            "status": l.status,
            "created": l.created_at.strftime("%Y-%m-%d") if l.created_at else ""
        })
    columns = ["name", "email", "status", "created"]
    return templates.TemplateResponse("list_view.html", {
        "request": {}, 
        "object_type": "Lead", 
        "items": items, 
        "columns": columns
    })

@router.get("/leads/new-modal")
async def new_lead_modal(request: Request, db: Session = Depends(get_db)):
    campaigns = CampaignService.get_campaigns(db)
    brands = VehicleSpecService.get_specs(db, record_type="Brand")
    models = VehicleSpecService.get_specs(db, record_type="Model")
    fields = ["first_name", "last_name", "gender", "email", "phone", "campaign_id", "brand_id", "model_interest_id", "description"]
    return templates.TemplateResponse("object_form.html", {
        "request": request,
        "object_type": "Lead",
        "campaigns": campaigns,
        "brands": brands,
        "models": models,
        "fields": fields
    })

@router.post("/leads")
async def create_lead(
    first_name: str = Form(...),
    last_name: str = Form(...),
    gender: str = Form(None),
    email: str = Form(...),
    phone: str = Form(None),
    campaign_id: str = Form(None),
    brand_id: str = Form(None),
    model_interest_id: str = Form(None),
    description: str = Form(None),
    db: Session = Depends(get_db)
):
    LeadService.create_lead(
        db, first_name=first_name, last_name=last_name, gender=gender,
        email=email, phone=phone, campaign_id=campaign_id,
        brand_id=brand_id, model_interest_id=model_interest_id,
        description=description, status="New"
    )
    return RedirectResponse(url="/leads", status_code=303)

@router.post("/leads/{lead_id}/convert")
async def convert_lead(lead_id: str, db: Session = Depends(get_db)):
    LeadService.convert_lead(db, lead_id)
    return RedirectResponse(url="/opportunities", status_code=303)

@router.get("/accounts/{account_id}")
async def account_detail(account_id: str, db: Session = Depends(get_db)):
    account = AccountService.get_account(db, account_id)
    if not account:
        return RedirectResponse(url="/accounts")
    
    # Details tab data
    details = {
        "Account_Name": account.name,
        "Record_Type": account.record_type,
        "Status": account.status,
        "Phone": account.phone,
        "Website": account.website,
        "Created_By": "Admin",
        "Created_Date": account.created_at.strftime("%Y-%m-%d %H:%M") if account.created_at else "N/A"
    }
    
    # Related tab data
    contacts = ContactService.get_contacts(db, account_id=account_id)
    opps = OpportunityService.get_by_account(db, account_id=account_id)
    assets = AssetService.get_by_account(db, account_id=account_id)
    
    related_lists = []
    if contacts:
        related_lists.append({
            "title": "Contacts",
            "columns": ["first_name", "last_name", "email", "phone"],
            "items": [{"first_name": c.first_name, "last_name": c.last_name, "email": c.email, "phone": c.phone} for c in contacts]
        })
    if opps:
        related_lists.append({
            "title": "Opportunities",
            "columns": ["name", "stage", "amount", "close_date"],
            "items": [{"name": o.name, "stage": o.stage, "amount": f"{o.amount:,} KRW", "close_date": o.close_date} for o in opps]
        })
    if assets:
        related_lists.append({
            "title": "Assets",
            "columns": ["name", "vin", "status"],
            "items": [{"name": a.name, "vin": a.vin, "status": a.status} for a in assets]
        })

    return templates.TemplateResponse("detail_view.html", {
        "request": {},
        "object_type": "Account",
        "record_name": account.name,
        "details": details,
        "related_lists": related_lists
    })
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
async def new_account_modal(request: Request, type: str = "Individual"):
    fields = ["name", "industry", "website", "status", "description"]
    return templates.TemplateResponse("object_form.html", {
        "request": request,
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
@router.get("/opportunities/{opp_id}")
async def opportunity_detail(opp_id: str, db: Session = Depends(get_db)):
    opp = OpportunityService.get_opportunity(db, opp_id)
    if not opp:
        return RedirectResponse(url="/opportunities")
    
    details = {
        "Opportunity_Name": opp.name,
        "Stage": opp.stage,
        "Amount": f"{opp.amount:,} KRW",
        "Close_Date": opp.close_date,
        "Account_Id": opp.account_id,
        "Created_Date": opp.created_at.strftime("%Y-%m-%d %H:%M") if opp.created_at else "N/A"
    }
    
    # Path/Progress bar
    stages = ["Prospecting", "Qualification", "Needs Analysis", "Value Proposition", "Closed Won", "Closed Lost"]
    path = []
    found_active = False
    for s in stages:
        is_active = (s == opp.stage)
        is_completed = not found_active and not is_active
        if is_active: found_active = True
        path.append({"label": s, "active": is_active, "completed": is_completed})

    return templates.TemplateResponse("detail_view.html", {
        "request": {},
        "object_type": "Opportunity",
        "record_name": opp.name,
        "details": details,
        "path": path,
        "related_lists": []
    })
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
            "status": o.status
        })
    columns = ["name", "amount", "stage", "status"]
    return templates.TemplateResponse("list_view.html", {
        "request": {}, 
        "object_type": "Opportunity", 
        "plural_type": "opportunities",
        "items": items, 
        "columns": columns
    })

@router.get("/opportunities/new-modal")
async def new_opportunity_modal(request: Request, db: Session = Depends(get_db)):
    accounts = AccountService.get_accounts(db)
    brands = VehicleSpecService.get_specs(db, record_type="Brand")
    models = VehicleSpecService.get_specs(db, record_type="Model")
    fields = ["account_id", "name", "amount", "stage", "status", "brand_id", "model_interest_id", "probability"]
    return templates.TemplateResponse("object_form.html", {
        "request": request,
        "object_type": "Opportunity",
        "plural_type": "opportunities",
        "accounts": accounts,
        "brands": brands,
        "models": models,
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
    brand_id: str = Form(None),
    model_interest_id: str = Form(None),
    db: Session = Depends(get_db)
):
    OpportunityService.create_opportunity(
        db, account_id=account_id, name=name, amount=amount, 
        stage=stage, status=status, probability=probability,
        brand_id=brand_id, model_interest_id=model_interest_id
    )
    return RedirectResponse(url="/opportunities", status_code=303)

# --- VEHICLE SPECIFICATIONS ---
@router.get("/vehicle_specifications/{spec_id}")
async def vehicle_spec_detail(spec_id: str, db: Session = Depends(get_db)):
    spec = VehicleSpecService.get_spec(db, spec_id)
    if not spec: return RedirectResponse(url="/vehicle_specifications")
    details = {
        "Name": spec.name,
        "Record_Type": spec.record_type,
        "Parent_Id": spec.parent_id,
        "Created_Date": spec.created_at.strftime("%Y-%m-%d %H:%M") if spec.created_at else "N/A"
    }
    return templates.TemplateResponse("detail_view.html", {
        "request": {}, "object_type": "Vehicle Specification", "record_name": spec.name,
        "details": details, "related_lists": []
    })
@router.get("/vehicle_specifications")
async def list_specs(db: Session = Depends(get_db)):
    specs = VehicleSpecService.get_specs(db)
    items = []
    for s in specs:
        items.append({
            "id": s.id,
            "name": s.name,
            "type": s.record_type,
            "description": s.description
        })
    columns = ["name", "type", "description"]
    return templates.TemplateResponse("list_view.html", {
        "request": {}, 
        "object_type": "VehicleSpecification", 
        "plural_type": "vehicle_specifications",
        "items": items, 
        "columns": columns
    })

@router.get("/vehicle_specifications/record-types")
async def spec_record_type_modal():
    return templates.TemplateResponse("spec_record_type.html", {"request": {}})

@router.get("/vehicle_specifications/new")
async def new_spec_modal(request: Request, type: str = "Brand", db: Session = Depends(get_db)):
    brands = VehicleSpecService.get_specs(db, record_type="Brand")
    fields = ["name", "description"]
    if type == "Model":
        fields.append("parent_id")
    return templates.TemplateResponse("object_form.html", {
        "request": request,
        "object_type": "VehicleSpecification",
        "plural_type": "vehicle_specifications",
        "record_type": type,
        "brands": brands,
        "fields": fields
    })

@router.post("/vehicle_specifications")
async def create_spec(
    name: str = Form(...),
    record_type: str = Form("Brand"),
    parent_id: str = Form(None),
    description: str = Form(None),
    db: Session = Depends(get_db)
):
    VehicleSpecService.create_spec(
        db, name=name, record_type=record_type, parent_id=parent_id, description=description
    )
    return RedirectResponse(url="/vehicle_specifications", status_code=303)

# --- CAMPAIGNS ---
@router.get("/campaigns/{campaign_id}")
async def campaign_detail(campaign_id: str, db: Session = Depends(get_db)):
    campaign = CampaignService.get_campaign(db, campaign_id)
    if not campaign: return RedirectResponse(url="/campaigns")
    details = {
        "Name": campaign.name,
        "Status": campaign.status,
        "Type": campaign.type,
        "Description": campaign.description,
        "Created_Date": campaign.created_at.strftime("%Y-%m-%d %H:%M") if campaign.created_at else "N/A"
    }
    return templates.TemplateResponse("detail_view.html", {
        "request": {}, "object_type": "Campaign", "record_name": campaign.name,
        "details": details, "related_lists": []
    })
@router.get("/campaigns")
async def list_campaigns(db: Session = Depends(get_db)):
    campaigns = CampaignService.get_campaigns(db)
    items = []
    for c in campaigns:
        items.append({
            "id": c.id,
            "name": c.name,
            "status": c.status,
            "type": c.type or "Social Media"
        })
    columns = ["name", "type", "status"]
    return templates.TemplateResponse("list_view.html", {
        "request": {}, 
        "object_type": "Campaign", 
        "items": items, 
        "columns": columns
    })

@router.get("/campaigns/new-modal")
async def new_campaign_modal(request: Request):
    fields = ["name", "type", "status", "description"]
    return templates.TemplateResponse("object_form.html", {
        "request": request,
        "object_type": "Campaign",
        "fields": fields
    })

@router.post("/campaigns")
async def create_campaign(
    name: str = Form(...),
    type: str = Form("Social Media"),
    status: str = Form("Planned"),
    description: str = Form(None),
    db: Session = Depends(get_db)
):
    CampaignService.create_campaign(db, name=name, type=type, status=status, description=description)
    return RedirectResponse(url="/campaigns", status_code=303)

# --- PRODUCTS ---
@router.get("/products/{product_id}")
async def product_detail(product_id: str, db: Session = Depends(get_db)):
    product = ProductService.get_product(db, product_id)
    if not product: return RedirectResponse(url="/products")
    details = {
        "Name": product.name,
        "Brand": product.brand,
        "Category": product.category,
        "Price": f"{product.base_price:,} KRW",
        "Description": product.description,
        "Created_Date": product.created_at.strftime("%Y-%m-%d %H:%M") if product.created_at else "N/A"
    }
    return templates.TemplateResponse("detail_view.html", {
        "request": {}, "object_type": "Product", "record_name": product.name,
        "details": details, "related_lists": []
    })
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
async def new_product_modal(request: Request):
    fields = ["name", "brand", "category", "base_price", "description"]
    return templates.TemplateResponse("object_form.html", {
        "request": request,
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
@router.get("/assets/{asset_id}")
async def asset_detail(asset_id: str, db: Session = Depends(get_db)):
    asset = AssetService.get_asset(db, asset_id)
    if not asset: return RedirectResponse(url="/assets")
    details = {
        "Name": asset.name,
        "VIN": asset.vin,
        "Status": asset.status,
        "Price": f"{asset.price:,} KRW",
        "Account_Id": asset.account_id,
        "Product_Id": asset.product_id,
        "Created_Date": asset.created_at.strftime("%Y-%m-%d %H:%M") if asset.created_at else "N/A"
    }
    return templates.TemplateResponse("detail_view.html", {
        "request": {}, "object_type": "Asset", "record_name": asset.name,
        "details": details, "related_lists": []
    })
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
async def new_asset_modal(request: Request, db: Session = Depends(get_db)):
    accounts = AccountService.get_accounts(db)
    fields = ["account_id", "name", "vin", "price"]
    return templates.TemplateResponse("object_form.html", {
        "request": request,
        "object_type": "Asset",
        "accounts": accounts,
        "fields": fields
    })

@router.post("/assets")
async def create_asset(
    account_id: str = Form(...),
    name: str = Form(...),
    vin: str = Form(None),
    price: int = Form(0),
    db: Session = Depends(get_db)
):
    AssetService.create_asset(
        db, account_id=account_id, name=name, vin=vin, price=price
    )
    return RedirectResponse(url="/assets", status_code=303)

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

@router.post("/seed")
async def seed_data(theme: str = Form(...), db: Session = Depends(get_db)):
    from ..services.seed_service import SeedService
    await SeedService.generate_theme_data(db, theme, count=5)
    return RedirectResponse(url="/", status_code=303)
