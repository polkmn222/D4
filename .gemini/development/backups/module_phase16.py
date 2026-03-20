
# FILE: app/models.py
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, CheckConstraint, Boolean
from sqlalchemy.sql import func
from .database import Base

class BaseModel(Base):
    __abstract__ = True
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class VehicleSpecification(BaseModel):
    __tablename__ = "vehicle_specifications"

    id = Column(String(18), primary_key=True, index=True)
    name = Column(String, nullable=False)
    record_type = Column(String, default="Model") # Brand, Model
    parent_id = Column(String(18), ForeignKey("vehicle_specifications.id"), nullable=True) # For Model -> Brand lookup
    description = Column(Text, nullable=True)

class Campaign(BaseModel):
    __tablename__ = "campaigns"

    id = Column(String(18), primary_key=True, index=True)
    name = Column(String, nullable=False)
    type = Column(String, nullable=True)
    status = Column(String, default="Planned")
    start_date = Column(DateTime, nullable=True)
    end_date = Column(DateTime, nullable=True)
    description = Column(Text, nullable=True)

class Account(BaseModel):
    __tablename__ = "accounts"

    id = Column(String(18), primary_key=True, index=True)
    name = Column(String, nullable=False)
    is_person_account = Column(Boolean, default=False)
    record_type = Column(String, default="Individual") # Individual, Corporate
    status = Column(String, default="Active") # Active, Inactive, Prospect
    industry = Column(String, nullable=True)
    website = Column(String, nullable=True)
    tier = Column(String, default="Bronze")
    description = Column(Text, nullable=True)

class Contact(BaseModel):
    __tablename__ = "contacts"

    id = Column(String(18), primary_key=True, index=True)
    account_id = Column(String(18), ForeignKey("accounts.id"), nullable=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    phone = Column(String, nullable=True)
    gender = Column(String, nullable=True)
    lead_source = Column(String, nullable=True)
    status = Column(String, default="New")
    description = Column(Text, nullable=True)
    ai_summary = Column(Text, nullable=True)
    last_interaction_at = Column(DateTime, nullable=True)

class Lead(BaseModel):
    __tablename__ = "leads"

    id = Column(String(18), primary_key=True, index=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    gender = Column(String, nullable=True)
    email = Column(String, index=True, nullable=False)
    phone = Column(String, nullable=True)
    status = Column(String, default="New") # New, Follow Up, Qualified, Lost
    is_converted = Column(Boolean, default=False)
    converted_account_id = Column(String(18), ForeignKey("accounts.id"), nullable=True)
    converted_opportunity_id = Column(String(18), ForeignKey("opportunities.id"), nullable=True)
    campaign_id = Column(String(18), ForeignKey("campaigns.id"), nullable=True)
    brand_id = Column(String(18), ForeignKey("vehicle_specifications.id"), nullable=True)
    model_interest_id = Column(String(18), ForeignKey("vehicle_specifications.id"), nullable=True)
    description = Column(Text, nullable=True)
    is_flow_enabled = Column(Boolean, default=False)

class Product(BaseModel):
    __tablename__ = "products"

    id = Column(String(18), primary_key=True, index=True)
    name = Column(String, nullable=False)
    brand = Column(String, default="Solaris") # Fictional
    category = Column(String, nullable=True)
    base_price = Column(Integer, default=0)
    description = Column(Text, nullable=True)

class Opportunity(BaseModel):
    __tablename__ = "opportunities"

    id = Column(String(18), primary_key=True, index=True)
    account_id = Column(String(18), ForeignKey("accounts.id"), nullable=False)
    product_id = Column(String(18), ForeignKey("products.id"), nullable=True)
    lead_id = Column(String(18), ForeignKey("leads.id"), nullable=True)
    brand_id = Column(String(18), ForeignKey("vehicle_specifications.id"), nullable=True)
    model_interest_id = Column(String(18), ForeignKey("vehicle_specifications.id"), nullable=True)
    name = Column(String, nullable=False)
    amount = Column(Integer, default=0)
    stage = Column(String, default="Prospecting")
    status = Column(String, default="Open") # Open, Closed Won, Closed Lost
    probability = Column(Integer, default=10)
    close_date = Column(DateTime, nullable=True)
    ai_insight = Column(Text, nullable=True)
    is_flow_enabled = Column(Boolean, default=False)

class Asset(BaseModel):
    __tablename__ = "assets"

    id = Column(String(18), primary_key=True, index=True)
    account_id = Column(String(18), ForeignKey("accounts.id"), nullable=False)
    product_id = Column(String(18), ForeignKey("products.id"), nullable=True)
    name = Column(String, nullable=False)
    vin = Column(String, unique=True, nullable=True)
    status = Column(String, default="Active")
    purchase_date = Column(DateTime, nullable=True)
    price = Column(Integer, default=0)

class Task(BaseModel):
    __tablename__ = "tasks"

    id = Column(String(18), primary_key=True, index=True)
    account_id = Column(String(18), ForeignKey("accounts.id"), nullable=False)
    subject = Column(String, nullable=False)
    status = Column(String, default="Not Started") # Not Started, In Progress, Completed
    priority = Column(String, default="Normal")
    description = Column(Text, nullable=True)
    due_date = Column(DateTime, nullable=True)

class Message(BaseModel):
    __tablename__ = "messages"

    id = Column(String(18), primary_key=True, index=True)
    contact_id = Column(String(18), ForeignKey("contacts.id"), nullable=False)
    direction = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    status = Column(String, default="Pending")
    provider_message_id = Column(String, nullable=True)
    sent_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        CheckConstraint(direction.in_(['Inbound', 'Outbound']), name='check_direction'),
    )

# END FILE

# FILE: app/database.py
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
import os
from dotenv import load_dotenv

load_dotenv()

SQLALCHEMY_DATABASE_URL = "sqlite:///./crm.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# END FILE

# FILE: app/utils/sf_id.py
import random
import string

def generate_sf_id(prefix: str) -> str:
    """
    Generates a Salesforce-like 18-character ID.
    Prefix should be 3 characters.
    """
    # 1. 15-character base (Prefix + 12 random chars)
    random_part = ''.join(random.choices(string.ascii_letters + string.digits, k=15 - len(prefix)))
    base_15 = prefix + random_part
    
    # 2. 3-character checksum
    # Divide into 3 chunks of 5
    chunks = [base_15[0:5], base_15[5:10], base_15[10:15]]
    lookup = "ABCDEFGHIJKLMNOPQRSTUVWXYZ012345"
    
    checksum = ""
    for chunk in chunks:
        val = 0
        for i, char in enumerate(chunk):
            if char in string.ascii_uppercase:
                val += (1 << i)
        checksum += lookup[val]
        
    return base_15 + checksum

# Object Prefixes
PREFIXES = {
    "Account": "001",
    "Contact": "003",
    "Opportunity": "006",
    "Lead": "00Q",
    "Product": "01t",
    "Asset": "02i",
    "Task": "00T",
    "Message": "00P",
    "Campaign": "701",
    "VehicleSpecification": "avS"
}

def get_id(object_type: str) -> str:
    prefix = PREFIXES.get(object_type, "000")
    return generate_sf_id(prefix)

# END FILE

# FILE: app/static/css/style.css
:root {
    --primary: #0070d2;
    --hover: #005fb2;
    --background: #f3f2f1;
    --surface: #ffffff;
    --text: #080707;
    --text-label: #3e3e3c;
    --border: #dddbda;
    --success: #2e844a;
    --error: #ea001e;
    --header-bg: #f3f3f3;
    --nav-blue: #0176d3;
    --shadow: 0 2px 2px 0 rgba(0,0,0,0.1);
    --radius: 0.25rem;
}

* { box-sizing: border-box; margin: 0; padding: 0; }
body { 
    font-family: 'Inter', -apple-system, system-ui, sans-serif; 
    background-color: var(--background);
    color: var(--text);
}

/* Header & Tab Bar */
.sf-header {
    background: white;
    border-bottom: 1px solid var(--border);
    padding: 0.5rem 1rem;
    display: flex;
    align-items: center;
    gap: 1.5rem;
}

.sf-tabs {
    background: white;
    display: flex;
    padding: 0 1rem;
    border-bottom: 3px solid var(--nav-blue);
}

.sf-tab {
    padding: 0.75rem 1rem;
    color: var(--text-label);
    text-decoration: none;
    font-size: 0.8125rem;
    font-weight: 500;
    border-top: 3px solid transparent;
}

.sf-tab.active {
    background: #eef4ff;
    border-top: 3px solid var(--nav-blue);
    color: var(--nav-blue);
}

/* Layout Grid */
.dashboard-grid {
    display: grid;
    grid-template-columns: 1fr 300px;
    gap: 1rem;
    padding: 1rem;
}

/* Salesforce Card Style */
.sf-card {
    background: white;
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 1rem;
    margin-bottom: 1rem;
}

.sf-card-header {
    font-size: 1rem;
    font-weight: 700;
    margin-bottom: 1rem;
    display: flex;
    justify-content: space-between;
}

/* Buttons */
.btn {
    padding: 0.375rem 0.75rem;
    border-radius: var(--radius);
    border: 1px solid var(--border);
    background: white;
    cursor: pointer;
    font-size: 0.8125rem;
    transition: 0.2s;
}

.btn-primary { background: var(--primary); color: white; border-color: var(--primary); }
.btn-primary:hover { background: var(--hover); }

/* Table */
.sf-table { width: 100%; border-collapse: collapse; }
.sf-table th { text-align: left; padding: 0.5rem; border-bottom: 1px solid var(--border); color: var(--text-label); font-size: 0.75rem; text-transform: uppercase; }
.sf-table td { padding: 0.75rem 0.5rem; border-bottom: 1px solid var(--border); font-size: 0.8125rem; }

/* Badge */
.badge { padding: 0.125rem 0.5rem; border-radius: 1rem; font-size: 0.7rem; font-weight: 700; }
.badge-new { background: #e0f0fd; color: #0070d2; }
/* Modal */
.sf-modal-overlay {
    position: fixed;
    top: 0; left: 0; right: 0; bottom: 0;
    background: rgba(8, 7, 7, 0.6);
    display: none;
    align-items: center;
    justify-content: center;
    z-index: 1000;
}

.sf-modal {
    background: white;
    width: 600px;
    max-width: 90%;
    border-radius: var(--radius);
    box-shadow: 0 12px 30px rgba(0,0,0,0.15);
    overflow: hidden;
    position: relative;
}

.sf-modal-header {
    padding: 1rem 1.5rem;
    border-bottom: 1px solid var(--border);
    display: flex;
    justify-content: space-between;
    align-items: center;
    background: #f3f3f3;
}

.sf-modal-body {
    padding: 2rem 1.5rem;
    max-height: 70vh;
    overflow-y: auto;
}

.sf-modal-footer {
    padding: 1rem 1.5rem;
    border-top: 1px solid var(--border);
    background: #f3f3f3;
    display: flex;
    justify-content: right;
    gap: 0.5rem;
}

.record-type-option {
    padding: 1rem;
    border: 1px solid var(--border);
    border-radius: var(--radius);
    margin-bottom: 1rem;
    cursor: pointer;
    transition: 0.2s;
}

.record-type-option:hover {
    border-color: var(--nav-blue);
    background: #f4f6f9;
}

.record-type-option.active {
    border-color: var(--nav-blue);
    box-shadow: 0 0 0 1px var(--nav-blue);
}

/* Detail View UI */
.detail-header {
    background: white;
    padding: 1rem 1.5rem;
    border-bottom: 1px solid var(--border);
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.detail-icon {
    width: 2.5rem;
    height: 2.5rem;
    background: #49a5e1;
    color: white;
    border-radius: var(--radius);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.5rem;
}

/* Salesforce Path (Progress Bar) */
.sf-path {
    display: flex;
    gap: 0.25rem;
    padding: 0.75rem 1.5rem;
    background: #f3f3f3;
}

.sf-path-item {
    flex: 1;
    padding: 0.5rem 1rem;
    background: white;
    clip-path: polygon(calc(100% - 10px) 0%, 100% 50%, calc(100% - 10px) 100%, 0% 100%, 10px 50%, 0% 0%);
    text-align: center;
    font-size: 0.75rem;
    font-weight: 600;
    color: var(--text-label);
    cursor: pointer;
    margin-left: -5px;
}

.sf-path-item:first-child { clip-path: polygon(calc(100% - 10px) 0%, 100% 50%, calc(100% - 10px) 100%, 0% 100%, 0% 0%); margin-left: 0; }
.sf-path-item.active { background: var(--nav-blue); color: white; }
.sf-path-item.completed { background: var(--success); color: white; }

/* In-Page Navigation Tabs */
.detail-tabs {
    background: white;
    border-bottom: 1px solid var(--border);
    display: flex;
    padding: 0 1.5rem;
}

.detail-tab {
    padding: 0.75rem 1rem;
    font-size: 0.8125rem;
    color: var(--text-label);
    cursor: pointer;
    border-bottom: 3px solid transparent;
}

.detail-tab.active {
    border-bottom-color: var(--nav-blue);
    font-weight: 700;
    color: var(--text);
}

/* Field Grid & Items */
.field-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 0 4rem;
}

.sf-field-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0.75rem 0;
    border-bottom: 1px solid var(--border);
    min-height: 4rem;
}

.sf-field-label {
    font-size: 0.75rem;
    color: var(--text-label);
    margin-bottom: 0.25rem;
}

.sf-field-value {
    font-size: 0.8125rem;
    font-weight: 500;
    color: var(--text);
}

.sf-pencil-icon {
    font-size: 0.875rem;
    color: var(--text-label);
    cursor: pointer;
    opacity: 0.3;
    transition: 0.2s;
    padding: 4px;
}

.sf-field-item:hover .sf-pencil-icon {
    opacity: 1;
}

/* Advanced Layout Refinements */
.sf-description-large {
    grid-column: span 2;
    margin-top: 1rem;
    padding: 1rem 0;
    border-bottom: 1px solid var(--border);
}

.sf-system-info {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 2rem;
    margin-top: 2rem;
    padding-top: 1rem;
    border-top: 2px solid var(--border);
}

.sf-system-user {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    font-size: 0.8125rem;
}

.sf-user-avatar {
    width: 1.5rem;
    height: 1.5rem;
    border-radius: 50%;
    background: #ccc;
    object-fit: cover;
}

/* Interactive Path Hover */
.sf-path-item:hover:not(.active):not(.completed) {
    background: #eef4ff;
    color: var(--nav-blue);
}

.sf-path-item.active {
    background: #00396b; /* Darker blue for active */
    color: white;
}

.sf-path-item.completed {
    background: #2e844a;
    color: white;
}

# END FILE

# FILE: app/api/web_router.py
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
        "plural_type": "contacts",
        "record_id": contact_id,
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
        "plural_type": "contacts",
        "items": items, 
        "columns": columns
    })

@router.get("/contacts/new-modal")
async def new_contact_modal(request: Request):
    fields = ["first_name", "last_name", "gender", "email", "phone", "description"]
    return templates.TemplateResponse("object_form.html", {
        "request": request,
        "object_type": "Contact",
        "plural_type": "contacts",
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

@router.post("/contacts/{contact_id}")
async def update_contact(
    contact_id: str,
    first_name: str = Form(...),
    last_name: str = Form(...),
    gender: str = Form(None),
    email: str = Form(...),
    phone: str = Form(None),
    description: str = Form(None),
    db: Session = Depends(get_db)
):
    ContactService.update_contact(
        db, contact_id, first_name=first_name, last_name=last_name, 
        gender=gender, email=email, phone=phone, description=description
    )
    return RedirectResponse(url=f"/contacts/{contact_id}", status_code=303)

@router.post("/contacts/{contact_id}/delete")
async def delete_contact(contact_id: str, db: Session = Depends(get_db)):
    ContactService.delete_contact(db, contact_id)
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
        "plural_type": "leads",
        "record_id": lead_id,
        "record_name": f"{lead.first_name} {lead.last_name}",
        "details": details,
        "path": path,
        "is_flow_enabled": lead.is_flow_enabled,
        "created_at": lead.created_at,
        "updated_at": lead.updated_at,
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
            "created": l.created_at.strftime("%Y-%m-%d") if l.created_at else "",
            "edit_url": f"/leads/new-modal?id={l.id}"
        })
    columns = ["name", "email", "status", "created"]
    return templates.TemplateResponse("list_view.html", {
        "request": {}, 
        "object_type": "Lead", 
        "plural_type": "leads",
        "items": items, 
        "columns": columns
    })

@router.get("/leads/new-modal")
async def new_lead_modal(request: Request, id: str = None, db: Session = Depends(get_db)):
    campaigns = CampaignService.get_campaigns(db)
    brands = VehicleSpecService.get_specs(db, record_type="Brand")
    models = VehicleSpecService.get_specs(db, record_type="Model")
    fields = ["first_name", "last_name", "gender", "email", "phone", "campaign_id", "brand_id", "model_interest_id", "description"]
    initial_values = None
    if id:
        lead = LeadService.get_lead(db, id)
        if lead:
            initial_values = {
                "id": lead.id,
                "first_name": lead.first_name,
                "last_name": lead.last_name,
                "gender": lead.gender,
                "email": lead.email,
                "phone": lead.phone,
                "campaign_id": lead.campaign_id,
                "brand_id": lead.brand_id,
                "model_interest_id": lead.model_interest_id,
                "description": lead.description
            }
    return templates.TemplateResponse("object_form.html", {
        "request": request,
        "object_type": "Lead",
        "plural_type": "leads",
        "campaigns": campaigns,
        "brands": brands,
        "models": models,
        "fields": fields,
        "initial_values": initial_values
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

@router.post("/leads/{lead_id}")
async def update_lead(
    lead_id: str,
    first_name: str = Form(...),
    last_name: str = Form(...),
    gender: str = Form(None),
    email: str = Form(...),
    phone: str = Form(None),
    description: str = Form(None),
    db: Session = Depends(get_db)
):
    LeadService.update_lead(db, lead_id, first_name=first_name, last_name=last_name, gender=gender, email=email, phone=phone, description=description)
    return RedirectResponse(url=f"/leads/{lead_id}", status_code=303)

@router.post("/leads/{lead_id}/delete")
async def delete_lead(lead_id: str, db: Session = Depends(get_db)):
    LeadService.delete_lead(db, lead_id)
    return RedirectResponse(url="/leads", status_code=303)

@router.post("/leads/{lead_id}/convert")
async def convert_lead(lead_id: str, db: Session = Depends(get_db)):
    LeadService.convert_lead(db, lead_id)
    return RedirectResponse(url="/opportunities", status_code=303)

@router.post("/leads/{lead_id}/stage")
async def update_lead_stage_endpoint(lead_id: str, stage: str = Form(...), db: Session = Depends(get_db)):
    LeadService.update_stage(db, lead_id, stage)
    return {"status": "success", "new_stage": stage}

@router.post("/leads/{lead_id}/toggle-flow")
async def toggle_lead_flow_endpoint(lead_id: str, enabled: bool = Form(...), db: Session = Depends(get_db)):
    LeadService.toggle_flow(db, lead_id, enabled)
    return {"status": "success", "flow_enabled": enabled}

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
        "Created_Date": account.created_at.strftime("%Y-%m-%d %H:%M") if account.created_at else "N/A",
        "Description": account.description
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
        "plural_type": "accounts",
        "record_id": account_id,
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
            "tier": a.tier,
            "edit_url": f"/accounts/new?type={a.record_type}&id={a.id}"
        })
    columns = ["name", "type", "status", "industry", "tier"]
    return templates.TemplateResponse("list_view.html", {
        "request": {}, 
        "object_type": "Account", 
        "plural_type": "accounts",
        "items": items, 
        "columns": columns
    })

@router.get("/accounts/record-types")
async def account_record_type_modal():
    return templates.TemplateResponse("account_record_type.html", {"request": {}})

@router.get("/accounts/new")
async def new_account_modal(request: Request, type: str = "Individual", id: str = None, db: Session = Depends(get_db)):
    fields = ["name", "industry", "website", "status", "description"]
    initial_values = None
    if id:
        acc = AccountService.get_account(db, id)
        if acc:
            initial_values = {
                "id": acc.id,
                "name": acc.name,
                "industry": acc.industry,
                "website": acc.website,
                "status": acc.status,
                "description": acc.description
            }
            type = acc.record_type
    return templates.TemplateResponse("object_form.html", {
        "request": request,
        "object_type": "Account",
        "plural_type": "accounts",
        "record_type": type,
        "fields": fields,
        "initial_values": initial_values
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

@router.post("/accounts/{account_id}")
async def update_account(
    account_id: str,
    name: str = Form(...),
    industry: str = Form(None),
    website: str = Form(None),
    status: str = Form(None),
    description: str = Form(None),
    db: Session = Depends(get_db)
):
    AccountService.update_account(db, account_id, name=name, industry=industry, website=website, status=status, description=description)
    return RedirectResponse(url=f"/accounts/{account_id}", status_code=303)

@router.post("/accounts/{account_id}/delete")
async def delete_account(account_id: str, db: Session = Depends(get_db)):
    AccountService.delete_account(db, account_id)
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
        "plural_type": "opportunities",
        "record_id": opp_id,
        "record_name": opp.name,
        "details": details,
        "path": path,
        "is_flow_enabled": opp.is_flow_enabled,
        "created_at": opp.created_at,
        "updated_at": opp.updated_at,
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
            "status": o.status,
            "edit_url": f"/opportunities/new-modal?id={o.id}"
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
async def new_opportunity_modal(request: Request, id: str = None, db: Session = Depends(get_db)):
    accounts = AccountService.get_accounts(db)
    brands = VehicleSpecService.get_specs(db, record_type="Brand")
    models = VehicleSpecService.get_specs(db, record_type="Model")
    fields = ["account_id", "name", "amount", "stage", "status", "brand_id", "model_interest_id", "probability"]
    initial_values = None
    if id:
        opp = OpportunityService.get_opportunity(db, id)
        if opp:
            initial_values = {
                "id": opp.id,
                "account_id": opp.account_id,
                "name": opp.name,
                "amount": opp.amount,
                "stage": opp.stage,
                "status": opp.status,
                "brand_id": opp.brand_id,
                "model_interest_id": opp.model_interest_id,
                "probability": opp.probability
            }
    return templates.TemplateResponse("object_form.html", {
        "request": request,
        "object_type": "Opportunity",
        "plural_type": "opportunities",
        "accounts": accounts,
        "brands": brands,
        "models": models,
        "fields": fields,
        "initial_values": initial_values
    })

@router.post("/opportunities/{opp_id}")
async def update_opportunity(
    opp_id: str,
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
    OpportunityService.update_opportunity(
        db, opp_id, account_id=account_id, name=name, amount=amount, 
        stage=stage, status=status, probability=probability,
        brand_id=brand_id, model_interest_id=model_interest_id
    )
    return RedirectResponse(url=f"/opportunities/{opp_id}", status_code=303)

@router.post("/opportunities/{opp_id}/delete")
async def delete_opportunity(opp_id: str, db: Session = Depends(get_db)):
    OpportunityService.delete_opportunity(db, opp_id)
    return RedirectResponse(url="/opportunities", status_code=303)

@router.post("/opportunities/{opp_id}/stage")
async def update_opportunity_stage_endpoint(opp_id: str, stage: str = Form(...), db: Session = Depends(get_db)):
    OpportunityService.update_stage(db, opp_id, stage)
    return {"status": "success", "new_stage": stage}

@router.post("/opportunities/{opp_id}/toggle-flow")
async def toggle_opportunity_flow_endpoint(opp_id: str, enabled: bool = Form(...), db: Session = Depends(get_db)):
    OpportunityService.toggle_flow(db, opp_id, enabled)
    return {"status": "success", "flow_enabled": enabled}

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
        "request": {}, 
        "object_type": "Vehicle Specification", 
        "plural_type": "vehicle_specifications",
        "record_id": spec_id,
        "record_name": spec.name,
        "details": details, 
        "related_lists": []
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
            "description": s.description,
            "edit_url": f"/vehicle_specifications/new?type={s.record_type}&id={s.id}"
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
async def new_spec_modal(request: Request, type: str = "Brand", id: str = None, db: Session = Depends(get_db)):
    brands = VehicleSpecService.get_specs(db, record_type="Brand")
    fields = ["name", "description"]
    if type == "Model":
        fields.append("parent_id")
    initial_values = None
    if id:
        spec = VehicleSpecService.get_spec(db, id)
        if spec:
            initial_values = {
                "id": spec.id,
                "name": spec.name,
                "record_type": spec.record_type,
                "parent_id": spec.parent_id,
                "description": spec.description
            }
            type = spec.record_type
    return templates.TemplateResponse("object_form.html", {
        "request": request,
        "object_type": "VehicleSpecification",
        "plural_type": "vehicle_specifications",
        "record_type": type,
        "brands": brands,
        "fields": fields,
        "initial_values": initial_values
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

@router.post("/vehicle_specifications/{spec_id}")
async def update_spec(
    spec_id: str,
    name: str = Form(...),
    record_type: str = Form("Brand"),
    parent_id: str = Form(None),
    description: str = Form(None),
    db: Session = Depends(get_db)
):
    # This spec service update is simple enough to do here or add to service
    spec = db.query(VehicleSpecification).filter(VehicleSpecification.id == spec_id).first()
    if spec:
        spec.name = name
        spec.record_type = record_type
        spec.parent_id = parent_id
        spec.description = description
        db.commit()
    return RedirectResponse(url=f"/vehicle_specifications/{spec_id}", status_code=303)

@router.post("/vehicle_specifications/{spec_id}/delete")
async def delete_spec(spec_id: str, db: Session = Depends(get_db)):
    spec = db.query(VehicleSpecification).filter(VehicleSpecification.id == spec_id).first()
    if spec:
        db.delete(spec)
        db.commit()
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
        "request": {}, 
        "object_type": "Campaign", 
        "plural_type": "campaigns",
        "record_id": campaign_id,
        "record_name": campaign.name,
        "details": details, 
        "related_lists": []
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
            "type": c.type or "Social Media",
            "edit_url": f"/campaigns/new-modal?id={c.id}"
        })
    columns = ["name", "type", "status"]
    return templates.TemplateResponse("list_view.html", {
        "request": {}, 
        "object_type": "Campaign", 
        "plural_type": "campaigns",
        "items": items, 
        "columns": columns
    })

@router.get("/campaigns/new-modal")
async def new_campaign_modal(request: Request, id: str = None, db: Session = Depends(get_db)):
    fields = ["name", "type", "status", "description"]
    initial_values = None
    if id:
        campaign = CampaignService.get_campaign(db, id)
        if campaign:
            initial_values = {
                "id": campaign.id,
                "name": campaign.name,
                "type": campaign.type,
                "status": campaign.status,
                "description": campaign.description
            }
    return templates.TemplateResponse("object_form.html", {
        "request": request,
        "object_type": "Campaign",
        "plural_type": "campaigns",
        "fields": fields,
        "initial_values": initial_values
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

@router.post("/campaigns/{campaign_id}")
async def update_campaign(
    campaign_id: str,
    name: str = Form(...),
    type: str = Form("Social Media"),
    status: str = Form("Planned"),
    description: str = Form(None),
    db: Session = Depends(get_db)
):
    campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    if campaign:
        campaign.name = name
        campaign.type = type
        campaign.status = status
        campaign.description = description
        db.commit()
    return RedirectResponse(url=f"/campaigns/{campaign_id}", status_code=303)

@router.post("/campaigns/{campaign_id}/delete")
async def delete_campaign(campaign_id: str, db: Session = Depends(get_db)):
    campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    if campaign:
        db.delete(campaign)
        db.commit()
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
        "request": {}, 
        "object_type": "Product", 
        "plural_type": "products",
        "record_id": product_id,
        "record_name": product.name,
        "details": details, 
        "related_lists": []
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
            "price": f"{p.base_price:,} KRW",
            "edit_url": f"/products/new-modal?id={p.id}"
        })
    columns = ["name", "brand", "category", "price"]
    return templates.TemplateResponse("list_view.html", {
        "request": {}, 
        "object_type": "Product", 
        "plural_type": "products",
        "items": items, 
        "columns": columns
    })

@router.get("/products/new-modal")
async def new_product_modal(request: Request, id: str = None, db: Session = Depends(get_db)):
    fields = ["name", "brand", "category", "base_price", "description"]
    initial_values = None
    if id:
        product = ProductService.get_product(db, id)
        if product:
            initial_values = {
                "id": product.id,
                "name": product.name,
                "brand": product.brand,
                "category": product.category,
                "base_price": product.base_price,
                "description": product.description
            }
    return templates.TemplateResponse("object_form.html", {
        "request": request,
        "object_type": "Product",
        "plural_type": "products",
        "fields": fields,
        "initial_values": initial_values
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

@router.post("/products/{product_id}")
async def update_product(
    product_id: str,
    name: str = Form(...),
    brand: str = Form("Solaris"),
    category: str = Form("SUV"),
    base_price: int = Form(0),
    description: str = Form(None),
    db: Session = Depends(get_db)
):
    product = db.query(Product).filter(Product.id == product_id).first()
    if product:
        product.name = name
        product.brand = brand
        product.category = category
        product.base_price = base_price
        product.description = description
        db.commit()
    return RedirectResponse(url=f"/products/{product_id}", status_code=303)

@router.post("/products/{product_id}/delete")
async def delete_product(product_id: str, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if product:
        db.delete(product)
        db.commit()
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
        "request": {}, 
        "object_type": "Asset", 
        "plural_type": "assets",
        "record_id": asset_id,
        "record_name": asset.name,
        "details": details, 
        "related_lists": []
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
            "price": f"{a.price:,} KRW",
            "edit_url": f"/assets/new-modal?id={a.id}"
        })
    columns = ["name", "vin", "status", "price"]
    return templates.TemplateResponse("list_view.html", {
        "request": {}, 
        "object_type": "Asset", 
        "plural_type": "assets",
        "items": items, 
        "columns": columns
    })

@router.get("/assets/new-modal")
async def new_asset_modal(request: Request, id: str = None, db: Session = Depends(get_db)):
    accounts = AccountService.get_accounts(db)
    fields = ["account_id", "name", "vin", "price"]
    initial_values = None
    if id:
        asset = AssetService.get_asset(db, id)
        if asset:
            initial_values = {
                "id": asset.id,
                "account_id": asset.account_id,
                "name": asset.name,
                "vin": asset.vin,
                "price": asset.price
            }
    return templates.TemplateResponse("object_form.html", {
        "request": request,
        "object_type": "Asset",
        "plural_type": "assets",
        "accounts": accounts,
        "fields": fields,
        "initial_values": initial_values
    })

@router.post("/assets/{asset_id}")
async def update_asset(
    asset_id: str,
    account_id: str = Form(...),
    name: str = Form(...),
    vin: str = Form(None),
    price: int = Form(0),
    db: Session = Depends(get_db)
):
    AssetService.update_asset(db, asset_id, account_id=account_id, name=name, vin=vin, price=price)
    return RedirectResponse(url=f"/assets/{asset_id}", status_code=303)

@router.post("/assets/{asset_id}/delete")
async def delete_asset(asset_id: str, db: Session = Depends(get_db)):
    AssetService.delete_asset(db, asset_id)
    return RedirectResponse(url="/assets", status_code=303)

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

# END FILE

# FILE: app/templates/list_view.html
{% extends "base.html" %}

{% block title %}{{ object_type }} List - Salesforce{% endblock %}

{% block content %}
<div style="background: white; border-bottom: 1px solid var(--border); padding: 1rem 1.5rem; display: flex; justify-content: space-between; align-items: center;">
    <div>
        <nav style="font-size: 0.75rem; color: var(--text-label); margin-bottom: 0.25rem;">
            {{ object_type }}s
        </nav>
        <h1 style="font-size: 1.25rem; font-weight: 700;">Recently Viewed</h1>
    </div>
    <div style="display: flex; gap: 0.5rem;">
        {% set p_type = plural_type if plural_type else (object_type|lower + 's') %}
        {% if object_type == 'Account' %}
        <button onclick="openModal('/accounts/record-types')" class="btn btn-primary">New</button>
        {% elif object_type == 'VehicleSpecification' %}
        <button onclick="openModal('/vehicle_specifications/record-types')" class="btn btn-primary">New</button>
        {% else %}
        <button onclick="openModal('/{{ p_type }}/new-modal')" class="btn btn-primary">New</button>
        {% endif %}
        <button onclick="openModal('/import-modal?object_type={{ object_type }}')" class="btn">Import</button>
        <button class="btn">Change Status</button>
    </div>
</div>

<div style="padding: 1rem;">
    <div class="sf-card" style="padding: 0;">
        <div style="padding: 0.5rem 1rem; border-bottom: 1px solid var(--border); display: flex; justify-content: space-between; align-items: center; background: #fafaf9;">
            <div style="font-size: 0.75rem; color: var(--text-label);">
                {{ items|length }} items • Updated a few seconds ago
            </div>
            <div style="display: flex; gap: 0.5rem;">
                <input type="text" placeholder="Search this list..." class="btn" style="width: 200px; text-align: left;">
                <button class="btn">⚙️</button>
            </div>
        </div>
        
        <table class="sf-table">
            <thead>
                <tr>
                    <th style="width: 40px;"><input type="checkbox"></th>
                    {% for col in columns %}
                    <th>{{ col.replace('_', ' ')|upper }}</th>
                    {% endfor %}
                    <th style="width: 100px;">ACTIONS</th>
                </tr>
            </thead>
            <tbody>
                {% for item in items %}
                <tr>
                    <td><input type="checkbox"></td>
                    {% for col in columns %}
                    <td>
                        {% if loop.first %}
                        <a href="/{{ p_type }}/{{ item.id }}" style="text-decoration: none;">
                            <strong style="color: var(--nav-blue);">{{ item[col] }}</strong>
                        </a>
                        {% else %}
                        {{ item[col] }}
                        {% endif %}
                    </td>
                    {% endfor %}
                    <td>
                        <div style="display: flex; gap: 0.5rem;">
                            {% if object_type == 'Lead' %}
                            <form action="/leads/{{ item.id }}/convert" method="POST" style="display:inline;">
                                <button type="submit" class="btn btn-primary" style="padding: 2px 8px; background: var(--success); border-color: var(--success);">Convert</button>
                            </form>
                            {% endif %}
                            <button onclick="openModal('{{ item.edit_url }}')" class="btn" style="padding: 2px 8px;">Edit</button>
                            <form action="/{{ p_type }}/{{ item.id }}/delete" method="POST" onsubmit="return confirm('Are you sure?');" style="display:inline;">
                                <button type="submit" class="btn" style="padding: 2px 8px; color: var(--error);">Del</button>
                            </form>
                        </div>
                    </td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
</div>
{% endblock %}

# END FILE

# FILE: app/templates/spec_record_type.html
<div class="sf-modal-header">
    <h2 style="font-size: 1.1rem; font-weight: 700;">New Vehicle Specification</h2>
    <span style="cursor: pointer;" onclick="closeModal()">✕</span>
</div>
<div class="sf-modal-body">
    <p style="margin-bottom: 1.5rem; color: var(--text-label); font-size: 0.875rem;">Select a record type</p>
    
    <label class="record-type-option" onclick="selectType('Brand')">
        <div style="display: flex; gap: 1rem; align-items: start;">
            <input type="radio" name="spec_type" value="Brand" checked>
            <div>
                <div style="font-weight: 700; font-size: 0.875rem;">Brand</div>
                <div style="font-size: 0.75rem; color: var(--text-label);">Represents a vehicle manufacturer (e.g., Solaris, Zenith).</div>
            </div>
        </div>
    </label>

    <label class="record-type-option" onclick="selectType('Model')">
        <div style="display: flex; gap: 1rem; align-items: start;">
            <input type="radio" name="spec_type" value="Model">
            <div>
                <div style="font-weight: 700; font-size: 0.875rem;">Model</div>
                <div style="font-size: 0.75rem; color: var(--text-label);">Represents a specific vehicle model linked to a brand.</div>
            </div>
        </div>
    </label>
</div>
<div class="sf-modal-footer">
    <button class="btn" onclick="closeModal()">Cancel</button>
    <button class="btn btn-primary" onclick="proceedToForm()">Next</button>
</div>

<script>
    let selectedType = 'Brand';
    function selectType(type) {
        selectedType = type;
        document.querySelectorAll('input[name="spec_type"]').forEach(input => {
            if (input.value === type) input.checked = true;
        });
    }
    function proceedToForm() {
        openModal('/vehicle_specifications/new?type=' + selectedType);
    }
</script>

# END FILE

# FILE: app/templates/import_modal.html
<div class="sf-modal-header">
    <h2 style="font-size: 1.1rem; font-weight: 700;">Import {{ object_type }}s</h2>
    <span style="cursor: pointer;" onclick="closeModal()">✕</span>
</div>
<form action="/import" method="POST" enctype="multipart/form-data">
    <div class="sf-modal-body">
        <input type="hidden" name="object_type" value="{{ object_type }}">
        <div style="border: 2px dashed var(--border); padding: 3rem 2rem; text-align: center; border-radius: var(--radius); background: #fafaf9;">
            <p style="margin-bottom: 1rem; font-size: 0.875rem;">Upload a CSV file to import records.</p>
            <input type="file" name="file" accept=".csv" required style="font-size: 0.8125rem;">
        </div>
        <div style="margin-top: 1rem; font-size: 0.75rem; color: var(--text-label);">
            <p><strong>Note:</strong> Ensure your CSV headers match the object fields.</p>
        </div>
    </div>
    <div class="sf-modal-footer">
        <button type="button" class="btn" onclick="closeModal()">Cancel</button>
        <button type="submit" class="btn btn-primary">Verify & Import</button>
    </div>
</form>

# END FILE

# FILE: app/templates/base.html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}AI CRM{% endblock %}</title>
    <link rel="stylesheet" href="/static/css/style.css">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap" rel="stylesheet">
</head>
<body>
    <header class="sf-header">
        <div style="font-size: 1.5rem;">⠿</div>
        <div style="font-weight: 700; color: var(--primary); font-size: 1.1rem;">Sales</div>
        <div style="flex-grow: 1;">
            <input type="text" placeholder="Search Setup..." class="btn" style="width: 300px; text-align: left; background: #f3f3f3;">
        </div>
    </header>
    <nav class="sf-tabs">
        <a href="/" class="sf-tab" id="nav-home">Home</a>
        <a href="/leads" class="sf-tab" id="nav-leads">Leads</a>
        <a href="/accounts" class="sf-tab" id="nav-accounts">Accounts</a>
        <a href="/contacts" class="sf-tab" id="nav-contacts">Contacts</a>
        <a href="/opportunities" class="sf-tab" id="nav-opportunities">Opportunities</a>
        <a href="/campaigns" class="sf-tab" id="nav-campaigns">Campaigns</a>
        <a href="/vehicle_specifications" class="sf-tab" id="nav-specs">Specifications</a>
        <a href="/products" class="sf-tab" id="nav-products">Products</a>
        <a href="/assets" class="sf-tab" id="nav-assets">Assets</a>
    </nav>
    <script>
        document.querySelectorAll('.sf-tab').forEach(tab => {
            if (window.location.pathname === tab.getAttribute('href')) {
                tab.classList.add('active');
            } else {
                tab.classList.remove('active');
            }
        });
    </script>
    <div id="sf-modal-overlay" class="sf-modal-overlay">
        <div class="sf-modal">
            <div id="modal-content"></div>
        </div>
    </div>

    <script>
        function openModal(url) {
            fetch(url)
                .then(response => response.text())
                .then(html => {
                    document.getElementById('modal-content').innerHTML = html;
                    document.getElementById('sf-modal-overlay').style.display = 'flex';
                });
        }

        function closeModal() {
            document.getElementById('sf-modal-overlay').style.display = 'none';
        }

        window.onclick = function(event) {
            if (event.target == document.getElementById('sf-modal-overlay')) {
                closeModal();
            }
        }
    </script>
    <main>
        {% block content %}{% endblock %}
    </main>
</body>
</html>

# END FILE

# FILE: app/templates/object_form.html
<div class="sf-modal-header">
    <h2 style="font-size: 1.1rem; font-weight: 700;">
        {% if initial_values %}Edit {{ object_type }}{% else %}New {{ object_type }}{% endif %}
        {% if record_type %}({{ record_type }}){% endif %}
    </h2>
    <span style="cursor: pointer;" onclick="closeModal()">✕</span>
</div>
{% set p_type = plural_type if plural_type else (object_type|lower + 's') %}
<form id="objectForm" action="/{{ p_type }}{% if initial_values and initial_values.id %}/{{ initial_values.id }}{% endif %}" method="POST" onsubmit="return validateForm(this)">
    <div id="form-error" style="display: none; background: #ea001e; color: white; padding: 0.5rem 1rem; margin: 0 1.5rem; border-radius: 4px; font-size: 0.8125rem;">
        Complete the required fields to continue.
    </div>
    <div class="sf-modal-body">
        <div style="display: grid; gap: 1rem;">
            {% if record_type %}
            <input type="hidden" name="record_type" value="{{ record_type }}">
            {% endif %}
            {% if initial_values and initial_values.id %}
            <input type="hidden" name="id" value="{{ initial_values.id }}">
            {% endif %}
            
            {% for field in fields %}
            <div style="display: flex; flex-direction: column; gap: 0.25rem;">
                <label style="font-size: 0.75rem; color: var(--text-label);">{{ field.replace('_', ' ')|capitalize }}</label>
                
                {% set val = initial_values[field] if initial_values else '' %}
                
                {% if field == 'account_id' %}
                <select name="account_id" class="btn" style="text-align: left;" required>
                    <option value="">-- Select Account --</option>
                    {% for acc in accounts %}
                    <option value="{{ acc.id }}" {% if val == acc.id %}selected{% endif %}>{{ acc.name }}</option>
                    {% endfor %}
                </select>
                {% elif field == 'contact_id' %}
                <select name="contact_id" class="btn" style="text-align: left;" required>
                    <option value="">-- Select Contact --</option>
                    {% for contact in contacts %}
                    <option value="{{ contact.id }}" {% if val == contact.id %}selected{% endif %}>{{ contact.first_name }} {{ contact.last_name }}</option>
                    {% endfor %}
                </select>
                {% elif field == 'campaign_id' %}
                <select name="campaign_id" class="btn" style="text-align: left;">
                    <option value="">-- Select Campaign --</option>
                    {% for cmp in campaigns %}
                    <option value="{{ cmp.id }}" {% if val == cmp.id %}selected{% endif %}>{{ cmp.name }}</option>
                    {% endfor %}
                </select>
                {% elif field == 'brand_id' %}
                <select name="brand_id" class="btn" style="text-align: left;">
                    <option value="">-- Select Brand --</option>
                    {% for brand in brands %}
                    <option value="{{ brand.id }}" {% if val == brand.id %}selected{% endif %}>{{ brand.name }}</option>
                    {% endfor %}
                </select>
                {% elif field == 'model_interest_id' or field == 'parent_id' %}
                <select name="{{ field }}" class="btn" style="text-align: left;">
                    <option value="">-- Select Model/Parent --</option>
                    {% for m in models %}
                    <option value="{{ m.id }}" {% if val == m.id %}selected{% endif %}>{{ m.name }}</option>
                    {% endfor %}
                    {% if field == 'parent_id' %}
                        {% for brand in brands %}
                        <option value="{{ brand.id }}" {% if val == brand.id %}selected{% endif %}>{{ brand.name }}</option>
                        {% endfor %}
                    {% endif %}
                </select>
                {% elif field == 'stage' %}
                <select name="stage" class="btn" style="text-align: left;">
                    {% for s in ["Prospecting", "Qualification", "Needs Analysis", "Value Proposition", "Closed Won", "Closed Lost"] %}
                    <option {% if val == s %}selected{% endif %}>{{ s }}</option>
                    {% endfor %}
                </select>
                {% elif field == 'status' and object_type == 'Lead' %}
                <select name="status" class="btn" style="text-align: left;">
                    {% for s in ["New", "Follow Up", "Qualified", "Lost"] %}
                    <option {% if val == s %}selected{% endif %}>{{ s }}</option>
                    {% endfor %}
                </select>
                {% elif field == 'gender' %}
                <select name="gender" class="btn" style="text-align: left;">
                    <option value="">-- Select Gender --</option>
                    {% for g in ["Male", "Female", "Other"] %}
                    <option {% if val == g %}selected{% endif %}>{{ g }}</option>
                    {% endfor %}
                </select>
                {% elif field == 'description' %}
                <textarea name="description" class="btn" style="text-align: left; height: 100px; resize: vertical;">{{ val }}</textarea>
                {% else %}
                <input type="text" name="{{ field }}" class="btn" style="text-align: left;" value="{{ val }}" required>
                {% endif %}
            </div>
            {% endfor %}
        </div>
    </div>
    <div class="sf-modal-footer">
        <button type="button" class="btn" onclick="closeModal()">Cancel</button>
        <button type="submit" class="btn btn-primary">Save</button>
    </div>
</form>

<script>
    function validateForm(form) {
        const errorBanner = document.getElementById('form-error');
        const inputs = form.querySelectorAll('input[required], select[required]');
        let valid = true;
        
        inputs.forEach(input => {
            if (!input.value.trim()) {
                input.style.borderColor = '#ea001e';
                valid = false;
            } else {
                input.style.borderColor = '';
            }
        });

        if (!valid) {
            errorBanner.style.display = 'block';
            return false;
        }
        return true;
    }
</script>

# END FILE

# FILE: app/templates/detail_view.html
{% extends "base.html" %}

{% block title %}{{ record_name }} | {{ object_type }} - Salesforce{% endblock %}

{% block content %}
<div class="detail-header">
    <div style="display: flex; gap: 1rem; align-items: center;">
        <div class="detail-icon" style="background: {% if object_type == 'Lead' %}#49a5e1{% elif object_type == 'Account' %}#7f8de1{% elif object_type == 'Contact' %}#a094ed{% else %}#fcb95b{% endif %};">
            {% if object_type == 'Lead' %}LQ{% elif object_type == 'Account' %}A{% elif object_type == 'Contact' %}C{% else %}O{% endif %}
        </div>
        <div>
            <nav style="font-size: 0.75rem; color: var(--text-label);">{{ object_type }}</nav>
            <h1 style="font-size: 1.25rem; font-weight: 700;">{{ record_name }}</h1>
        </div>
    </div>
    <div style="display: flex; gap: 0.5rem; align-items: center;">
        {% if object_type in ['Lead', 'Opportunity'] %}
        <button id="flow-btn" class="btn {% if is_flow_enabled %}btn-primary{% endif %}" onclick="toggleFlow('{{plural_type}}', '{{record_id}}', {{ 'true' if is_flow_enabled else 'false' }})">
            Flow
        </button>
        {% endif %}
        <button class="btn" onclick="openModal('/{{ plural_type }}/new-modal?id={{ record_id }}')">Edit</button>
        <form action="/{{ plural_type }}/{{ record_id }}/delete" method="POST" onsubmit="return confirm('Are you sure you want to delete this record?');">
            <button type="submit" class="btn" style="color: var(--error);">Delete</button>
        </form>
        <button class="btn btn-primary">Follow</button>
    </div>
</div>

{% if path %}
<div class="sf-path-container" style="display: flex; align-items: center; background: #f3f3f3; padding: 0.5rem 1rem; gap: 0.5rem;">
    <div class="sf-path" style="flex-grow: 1;">
        {% for step in path %}
        <div class="sf-path-item {% if step.active %}active{% elif step.completed %}completed{% endif %}" 
             onclick="updateStage(this, '{{plural_type}}', '{{record_id}}', '{{step.label}}')">
            {{ step.label }}
        </div>
        {% endfor %}
    </div>
    <button class="btn btn-primary" style="border-radius: 20px;">Mark Status as Complete</button>
</div>
{% endif %}

<div class="detail-tabs" style="margin-top: 0.5rem;">
    <div class="detail-tab active" onclick="switchTab('details')">Details</div>
    <div class="detail-tab" onclick="switchTab('related')">Related</div>
    <div class="detail-tab" onclick="switchTab('activity')">Activity</div>
</div>

<div id="tab-details" class="sf-card" style="margin: 1.5rem; display: block; padding: 1.5rem 2.5rem;">
    <div class="field-grid">
        {% for field, value in details.items() %}
        {% if field != 'Description' %}
        <div class="sf-field-item">
            <div>
                <div class="sf-field-label">{{ field.replace('_', ' ')|capitalize }}</div>
                <div class="sf-field-value">{{ value if value is not none else 'N/A' }}</div>
            </div>
            <div class="sf-pencil-icon" onclick="openModal('/{{ plural_type }}/new-modal?id={{ record_id }}')">✏️</div>
        </div>
        {% endif %}
        {% endfor %}

        <!-- Full-width Description -->
        <div class="sf-description-large">
            <div class="sf-field-label">Description</div>
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div class="sf-field-value" style="font-weight: 400; line-height: 1.5;">{{ details.get('Description', 'N/A') }}</div>
                <div class="sf-pencil-icon" onclick="openModal('/{{ plural_type }}/new-modal?id={{ record_id }}')">✏️</div>
            </div>
        </div>
    </div>

    <!-- System Info Section -->
    <div class="sf-system-info">
        <div>
            <div class="sf-field-label">Created By</div>
            <div class="sf-system-user">
                <img src="https://www.gravatar.com/avatar/00000000000000000000000000000000?d=mp&f=y" class="sf-user-avatar">
                <span style="color: var(--nav-blue); cursor: pointer;">admin</span>, 
                {{ created_at.strftime("%Y. %-m. %-d. %p %I:%M") if created_at else "N/A" }}
            </div>
        </div>
        <div>
            <div class="sf-field-label">Last Modified By</div>
            <div class="sf-system-user">
                <img src="https://www.gravatar.com/avatar/00000000000000000000000000000000?d=mp&f=y" class="sf-user-avatar">
                <span style="color: var(--nav-blue); cursor: pointer;">admin</span>, 
                {{ updated_at.strftime("%Y. %-m. %-d. %p %I:%M") if updated_at else "N/A" }}
            </div>
        </div>
    </div>
</div>

<div id="tab-related" class="sf-card" style="margin: 1.5rem; display: none;">
    <h3 style="font-size: 1rem; margin-bottom: 1rem; padding: 1rem;">Related Lists</h3>
    {% if related_lists %}
        {% for list in related_lists %}
        <div style="margin-bottom: 2rem; border: 1px solid var(--border); border-radius: 4px; overflow: hidden;">
            <div class="sf-card-header" style="background: #f3f3f3; padding: 0.5rem 1rem; margin-bottom: 0;">
                <span>{{ list.title }} ({{ list.items|length }})</span>
                <button class="btn">New</button>
            </div>
            <table class="sf-table">
                <thead>
                    <tr>
                        {% for col in list.columns %}
                        <th>{{ col|upper }}</th>
                        {% endfor %}
                    </tr>
                </thead>
                <tbody>
                    {% for item in list.items %}
                    <tr>
                        {% for col in list.columns %}
                        <td>{{ item[col.lower()] }}</td>
                        {% endfor %}
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
        {% endfor %}
    {% else %}
        <p style="color: var(--text-label); font-size: 0.875rem; padding: 1rem;">No related records found.</p>
    {% endif %}
</div>

<div id="tab-activity" class="sf-card" style="margin: 1.5rem; display: none; padding: 1rem;">
    <p style="color: var(--text-label); font-size: 0.875rem;">Activity Timeline Placeholder</p>
</div>

<script>
    function switchTab(tabName) {
        document.querySelectorAll('.detail-tab').forEach(t => t.classList.remove('active'));
        document.querySelectorAll('.sf-card').forEach(c => {
            if (c.id.startsWith('tab-')) c.style.display = 'none';
        });
        
        event.currentTarget.classList.add('active');
        document.getElementById('tab-' + tabName).style.display = 'block';
    }

    async function updateStage(el, type, id, stage) {
        const formData = new FormData();
        formData.append('stage', stage);
        
        const response = await fetch(`/${type}/${id}/stage`, {
            method: 'POST',
            body: formData
        });
        
        if (response.ok) {
            // Quick refresh or local UI update
            window.location.reload();
        }
    }

    async function toggleFlow(type, id, currentState) {
        const newState = !currentState;
        const formData = new FormData();
        formData.append('enabled', newState);
        
        const response = await fetch(`/${type}/${id}/toggle-flow`, {
            method: 'POST',
            body: formData
        });
        
        if (response.ok) {
            window.location.reload();
        }
    }
</script>
{% endblock %}

# END FILE

# FILE: app/templates/dashboard.html
{% extends "base.html" %}

{% block title %}Salesforce Home - AI CRM{% endblock %}

{% block content %}
<div class="dashboard-grid">
    <!-- Main Content Area -->
    <div class="main-column">
        <!-- Send Messages Card (From Screenshot) -->
        <div class="sf-card" style="text-align: center; padding: 4rem 2rem; background: linear-gradient(180deg, #b3d7ff 0%, #ffffff 100%);">
            <h2 style="font-size: 2rem; margin-bottom: 2rem; font-weight: 400;">Send Messages</h2>
            <form action="/messaging/start" method="POST">
                <button type="submit" class="btn btn-primary" style="padding: 0.75rem 2.5rem; font-size: 1.1rem;">Start Messages</button>
            </form>
        </div>

        <!-- Quarterly Performance (Placeholder) -->
        <div class="sf-card">
            <div class="sf-card-header">
                <span>Quarterly Performance</span>
            </div>
            <div style="border-top: 1px solid var(--border); padding-top: 1rem; display: flex; gap: 2rem;">
                <div><small style="color: var(--text-label)">CLOSED</small><br><strong>KRW 0</strong></div>
                <div><small style="color: var(--text-label)">OPEN (>70%)</small><br><strong>KRW 0</strong></div>
            </div>
            <div style="height: 150px; background: #f9f9f9; margin-top: 1rem; border-radius: 4px; border: 1px dashed #ccc; display: flex; align-items: center; justify-content: center; color: #999;">
                Chart visualization placeholder
            </div>
        </div>

        <!-- Contact List (Existing) -->
        <div class="sf-card">
            <div class="sf-card-header">
                <span>Recent Contacts</span>
            </div>
            <table class="sf-table">
                <thead>
                    <tr>
                        <th>Name</th>
                        <th>Email</th>
                        <th>Status</th>
                        <th>AI Summary</th>
                    </tr>
                </thead>
                <tbody>
                    {% for contact in contacts %}
                    <tr>
                        <td><strong>{{ contact.first_name }} {{ contact.last_name }}</strong></td>
                        <td>{{ contact.email }}</td>
                        <td><span class="badge badge-{{ contact.status|lower }}">{{ contact.status }}</span></td>
                        <td><small>{{ contact.ai_summary or 'No summary' }}</small></td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>

    <!-- Sidebar Area -->
    <div class="sidebar-column">
        <div class="sf-card">
            <div class="sf-card-header">Recent Records</div>
            <ul style="list-style: none;">
                {% for contact in contacts[:5] %}
                <li style="margin-bottom: 0.75rem; display: flex; align-items: center; gap: 0.5rem;">
                    <div style="width: 24px; height: 24px; background: #f38b00; border-radius: 4px; display: flex; align-items: center; justify-content: center; color: white; font-size: 0.7rem;">C</div>
                    <a href="#" style="text-decoration: none; color: var(--nav-blue); font-size: 0.85rem;">{{ contact.last_name }}</a>
                </li>
                {% endfor %}
            </ul>
        </div>

        <div class="sf-card">
            <div class="sf-card-header">AI Seed Data (Theme)</div>
            <form action="/seed" method="POST">
                <input type="text" name="theme" placeholder="e.g. Medical, Real Estate" class="btn" style="width: 100%; text-align: left; margin-bottom: 0.5rem;">
                <button type="submit" class="btn btn-primary" style="width: 100%;">Generate AI Data</button>
            </form>
        </div>
    </div>
</div>
{% endblock %}

# END FILE

# FILE: app/templates/contact_form.html
{% extends "base.html" %}

{% block title %}{{ 'Edit' if contact else 'New' }} Contact - AI CRM{% endblock %}

{% block content %}
<div class="card" style="max-width: 800px; margin: 0 auto;">
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 2rem; border-bottom: 1px solid var(--border); padding-bottom: 1rem;">
        <h2>{{ 'Edit Contact' if contact else 'Create New Contact' }}</h2>
        <a href="/" class="btn">Back to Dashboard</a>
    </div>

    <form action="{{ '/contacts/' + (contact.id|string) + '/edit' if contact else '/contacts/new' }}" method="POST">
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1.5rem;">
            <div class="form-group">
                <label for="first_name" style="display: block; margin-bottom: 0.5rem; color: var(--text-secondary); font-size: 0.875rem;">First Name</label>
                <input type="text" id="first_name" name="first_name" value="{{ contact.first_name if contact else '' }}" required class="btn" style="width: 100%; text-align: left;">
            </div>
            <div class="form-group">
                <label for="last_name" style="display: block; margin-bottom: 0.5rem; color: var(--text-secondary); font-size: 0.875rem;">Last Name</label>
                <input type="text" id="last_name" name="last_name" value="{{ contact.last_name if contact else '' }}" required class="btn" style="width: 100%; text-align: left;">
            </div>
            <div class="form-group">
                <label for="email" style="display: block; margin-bottom: 0.5rem; color: var(--text-secondary); font-size: 0.875rem;">Email Address</label>
                <input type="email" id="email" name="email" value="{{ contact.email if contact else '' }}" required class="btn" style="width: 100%; text-align: left;">
            </div>
            <div class="form-group">
                <label for="phone" style="display: block; margin-bottom: 0.5rem; color: var(--text-secondary); font-size: 0.875rem;">Phone Number</label>
                <input type="text" id="phone" name="phone" value="{{ contact.phone if contact else '' }}" class="btn" style="width: 100%; text-align: left;">
            </div>
            <div class="form-group">
                <label for="lead_source" style="display: block; margin-bottom: 0.5rem; color: var(--text-secondary); font-size: 0.875rem;">Lead Source</label>
                <select id="lead_source" name="lead_source" class="btn" style="width: 100%; text-align: left; appearance: none;">
                    <option value="Web" {{ 'selected' if contact and contact.lead_source == 'Web' else '' }}>Web</option>
                    <option value="Referral" {{ 'selected' if contact and contact.lead_source == 'Referral' else '' }}>Referral</option>
                    <option value="Manual" {{ 'selected' if contact and contact.lead_source == 'Manual' or not contact else '' }}>Manual</option>
                </select>
            </div>
            <div class="form-group">
                <label for="status" style="display: block; margin-bottom: 0.5rem; color: var(--text-secondary); font-size: 0.875rem;">Status</label>
                <select id="status" name="status" class="btn" style="width: 100%; text-align: left; appearance: none;">
                    <option value="New" {{ 'selected' if contact and contact.status == 'New' or not contact else '' }}>New</option>
                    <option value="Contacted" {{ 'selected' if contact and contact.status == 'Contacted' else '' }}>Contacted</option>
                    <option value="Qualified" {{ 'selected' if contact and contact.status == 'Qualified' else '' }}>Qualified</option>
                    <option value="Junk" {{ 'selected' if contact and contact.status == 'Junk' else '' }}>Junk</option>
                </select>
            </div>
        </div>

        <div class="form-group" style="margin-top: 1.5rem;">
            <label for="description" style="display: block; margin-bottom: 0.5rem; color: var(--text-secondary); font-size: 0.875rem;">Client Description (AI will use this for summary)</label>
            <textarea id="description" name="description" rows="5" class="btn" style="width: 100%; text-align: left; height: auto; min-height: 120px; resize: vertical;">{{ contact.description if contact else '' }}</textarea>
        </div>

        <div style="margin-top: 2rem; display: flex; justify-content: flex-end; gap: 1rem; border-top: 1px solid var(--border); padding-top: 1.5rem;">
            <button type="submit" class="btn btn-primary" style="padding: 0.75rem 2rem; font-weight: 600;">Save Contact</button>
        </div>
    </form>
</div>
{% endblock %}

# END FILE

# FILE: app/templates/account_record_type.html
<div class="sf-modal-header">
    <h2 style="font-size: 1.1rem; font-weight: 700;">New Account</h2>
    <span style="cursor: pointer;" onclick="closeModal()">✕</span>
</div>
<div class="sf-modal-body">
    <p style="margin-bottom: 1.5rem; color: var(--text-label); font-size: 0.875rem;">Select a record type</p>
    
    <label class="record-type-option" onclick="selectType('Individual')">
        <div style="display: flex; gap: 1rem; align-items: start;">
            <input type="radio" name="record_type" value="Individual" checked>
            <div>
                <div style="font-weight: 700; font-size: 0.875rem;">Individual</div>
                <div style="font-size: 0.75rem; color: var(--text-label);">Represents a single person. Personal account for individual retail customers.</div>
            </div>
        </div>
    </label>

    <label class="record-type-option" onclick="selectType('Corporate')">
        <div style="display: flex; gap: 1rem; align-items: start;">
            <input type="radio" name="record_type" value="Corporate">
            <div>
                <div style="font-weight: 700; font-size: 0.875rem;">Corporate</div>
                <div style="font-size: 0.75rem; color: var(--text-label);">Represents a business, organization, or institution. Used for fleet or commercial sales.</div>
            </div>
        </div>
    </label>
</div>
<div class="sf-modal-footer">
    <button class="btn" onclick="closeModal()">Cancel</button>
    <button class="btn btn-primary" onclick="proceedToForm()">Next</button>
</div>

<script>
    let selectedType = 'Individual';
    function selectType(type) {
        selectedType = type;
        document.querySelectorAll('input[name="record_type"]').forEach(input => {
            if (input.value === type) input.checked = true;
        });
    }
    function proceedToForm() {
        openModal('/accounts/new?type=' + selectedType);
    }
</script>

# END FILE

# FILE: app/main.py
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from .api.web_router import router as web_router
from .database import engine, Base
from . import models

app = FastAPI(title="AI Ready CRM")

# Mount Static Files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)

# Include Web Router
app.include_router(web_router)

# END FILE

# FILE: app/services/opportunity_service.py
from sqlalchemy.orm import Session
from ..models import Opportunity
from ..utils.sf_id import get_id
from typing import List, Optional

class OpportunityService:
    @staticmethod
    def create_opportunity(db: Session, account_id: str, name: str, amount: int, stage: str, status: str = "Open", probability: int = 10, **kwargs) -> Opportunity:
        db_opp = Opportunity(
            id=get_id("Opportunity"),
            account_id=account_id,
            name=name,
            amount=amount,
            stage=stage,
            status=status,
            probability=probability,
            **kwargs
        )
        db.add(db_opp)
        db.commit()
        db.refresh(db_opp)
        return db_opp

    @staticmethod
    def get_opportunities(db: Session) -> List[Opportunity]:
        return db.query(Opportunity).all()

    @staticmethod
    def get_opportunity(db: Session, opp_id: str) -> Optional[Opportunity]:
        return db.query(Opportunity).filter(Opportunity.id == opp_id).first()

    @staticmethod
    def update_opportunity(db: Session, opp_id: str, **kwargs) -> Optional[Opportunity]:
        db_opp = db.query(Opportunity).filter(Opportunity.id == opp_id).first()
        if db_opp:
            for key, value in kwargs.items():
                setattr(db_opp, key, value)
            db.commit()
            db.refresh(db_opp)
        return db_opp

    @staticmethod
    def delete_opportunity(db: Session, opp_id: str) -> bool:
        db_opp = db.query(Opportunity).filter(Opportunity.id == opp_id).first()
        if db_opp:
            db.delete(db_opp)
            db.commit()
            return True
        return False

    @staticmethod
    def update_stage(db: Session, opp_id: str, stage: str) -> Optional[Opportunity]:
        db_opp = db.query(Opportunity).filter(Opportunity.id == opp_id).first()
        if db_opp:
            db_opp.stage = stage
            db.commit()
            db.refresh(db_opp)
        return db_opp

    @staticmethod
    def toggle_flow(db: Session, opp_id: str, enabled: bool) -> Optional[Opportunity]:
        db_opp = db.query(Opportunity).filter(Opportunity.id == opp_id).first()
        if db_opp:
            db_opp.is_flow_enabled = enabled
            db.commit()
            db.refresh(db_opp)
        return db_opp

    @staticmethod
    def get_by_account(db: Session, account_id: str) -> List[Opportunity]:
        return db.query(Opportunity).filter(Opportunity.account_id == account_id).all()

# END FILE

# FILE: app/services/ai_service.py
import os
import httpx
from dotenv import load_dotenv

load_dotenv()

CEREBRAS_API_KEY = os.getenv("CELEBRACE_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

class AIService:
    @staticmethod
    async def generate_summary(description: str) -> str:
        if not description:
            return ""
        
        # Prefer Cerebras for fast real-time summaries as requested
        api_key = CEREBRAS_API_KEY
        base_url = "https://api.cerebras.ai/v1/chat/completions"
        model = "llama3.1-8b" # Standard fast model on Cerebras

        # Fallback to Groq if Cerebras is not configured
        if not api_key:
            api_key = GROQ_API_KEY
            base_url = "https://api.groq.com/openai/v1/chat/completions"
            model = "llama-3.3-70b-versatile"

        if not api_key:
            return "AI Summary unavailable (API Key missing)"

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    base_url,
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": model,
                        "messages": [
                            {"role": "system", "content": "You are a professional CRM assistant. Summarize the following customer description into a concise one-line summary (max 100 characters) in Korean if possible, or English if not."},
                            {"role": "user", "content": description}
                        ],
                        "max_tokens": 50
                    },
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return data["choices"][0]["message"]["content"].strip()
                else:
                    return f"AI Error: {response.status_code}"
        except Exception as e:
            return f"AI Service Error: {str(e)}"

# END FILE

# FILE: app/services/lead_service.py
from sqlalchemy.orm import Session
from ..models import Lead, Account, Opportunity, Contact
from ..utils.sf_id import get_id
from typing import List, Optional

class LeadService:
    @staticmethod
    def create_lead(db: Session, **kwargs) -> Lead:
        db_lead = Lead(id=get_id("Lead"), **kwargs)
        db.add(db_lead)
        db.commit()
        db.refresh(db_lead)
        return db_lead

    @staticmethod
    def get_leads(db: Session, converted: bool = False) -> List[Lead]:
        return db.query(Lead).filter(Lead.is_converted == converted).all()

    @staticmethod
    def get_lead(db: Session, lead_id: str) -> Optional[Lead]:
        return db.query(Lead).filter(Lead.id == lead_id).first()

    @staticmethod
    def update_lead(db: Session, lead_id: str, **kwargs) -> Optional[Lead]:
        db_lead = db.query(Lead).filter(Lead.id == lead_id).first()
        if db_lead:
            for key, value in kwargs.items():
                setattr(db_lead, key, value)
            db.commit()
            db.refresh(db_lead)
        return db_lead

    @staticmethod
    def delete_lead(db: Session, lead_id: str) -> bool:
        db_lead = db.query(Lead).filter(Lead.id == lead_id).first()
        if db_lead:
            db.delete(db_lead)
            db.commit()
            return True
        return False

    @staticmethod
    def update_stage(db: Session, lead_id: str, stage: str) -> Optional[Lead]:
        db_lead = db.query(Lead).filter(Lead.id == lead_id).first()
        if db_lead:
            db_lead.status = stage
            db.commit()
            db.refresh(db_lead)
        return db_lead

    @staticmethod
    def toggle_flow(db: Session, lead_id: str, enabled: bool) -> Optional[Lead]:
        db_lead = db.query(Lead).filter(Lead.id == lead_id).first()
        if db_lead:
            db_lead.is_flow_enabled = enabled
            db.commit()
            db.refresh(db_lead)
        return db_lead

    @staticmethod
    def convert_lead(db: Session, lead_id: str, product_id: Optional[str] = None) -> Optional[Account]:
        lead = db.query(Lead).filter(Lead.id == lead_id).first()
        if not lead or lead.is_converted:
            return None

        # 1. Create Account (Always Individual as per company removal, unless user specifies record_type later)
        is_person = True
        acc_name = f"{lead.first_name} {lead.last_name}"
        
        account = Account(
            id=get_id("Account"),
            name=acc_name,
            is_person_account=is_person,
            record_type="Individual",
            description=f"Converted from Lead: {lead.first_name} {lead.last_name}"
        )
        db.add(account)

        # 2. Create Contact
        contact = Contact(
            id=get_id("Contact"),
            account_id=account.id,
            first_name=lead.first_name,
            last_name=lead.last_name,
            email=lead.email,
            phone=lead.phone,
            gender=lead.gender,
            description=lead.description
        )
        db.add(contact)

        # 3. Create Opportunity (Inherit Brand/Model interest)
        opportunity = Opportunity(
            id=get_id("Opportunity"),
            account_id=account.id,
            product_id=product_id,
            lead_id=lead.id,
            brand_id=lead.brand_id,
            model_interest_id=lead.model_interest_id,
            name=f"{acc_name} - New Deal",
            amount=0,
            stage="Qualification",
            status="Open"
        )
        db.add(opportunity)

        # 4. Mark Lead as converted
        lead.is_converted = True
        lead.converted_account_id = account.id
        lead.converted_opportunity_id = opportunity.id
        lead.status = "Qualified" # Following the new status options

        db.commit()
        db.refresh(account)
        return account

# END FILE

# FILE: app/services/vehicle_spec_service.py
from sqlalchemy.orm import Session
from ..models import VehicleSpecification
from ..utils.sf_id import get_id
from typing import List, Optional

class VehicleSpecService:
    @staticmethod
    def create_spec(db: Session, **kwargs) -> VehicleSpecification:
        db_spec = VehicleSpecification(id=get_id("VehicleSpecification"), **kwargs)
        db.add(db_spec)
        db.commit()
        db.refresh(db_spec)
        return db_spec

    @staticmethod
    def get_specs(db: Session, record_type: Optional[str] = None) -> List[VehicleSpecification]:
        query = db.query(VehicleSpecification)
        if record_type:
            query = query.filter(VehicleSpecification.record_type == record_type)
        return query.all()

    @staticmethod
    def get_spec(db: Session, spec_id: str) -> Optional[VehicleSpecification]:
        return db.query(VehicleSpecification).filter(VehicleSpecification.id == spec_id).first()

# END FILE

# FILE: app/services/task_service.py
from sqlalchemy.orm import Session
from ..models import Task
from ..utils.sf_id import get_id
from typing import List, Optional

class TaskService:
    @staticmethod
    def create_task(db: Session, account_id: str, subject: str, **kwargs) -> Task:
        db_task = Task(id=get_id("Task"), account_id=account_id, subject=subject, **kwargs)
        db.add(db_task)
        db.commit()
        db.refresh(db_task)
        return db_task

    @staticmethod
    def get_tasks(db: Session, account_id: Optional[str] = None) -> List[Task]:
        query = db.query(Task)
        if account_id:
            query = query.filter(Task.account_id == account_id)
        return query.all()

# END FILE

# FILE: app/services/account_service.py
from sqlalchemy.orm import Session
from ..models import Account
from ..utils.sf_id import get_id
from typing import List, Optional

class AccountService:
    @staticmethod
    def create_account(db: Session, status: str = "Active", **kwargs) -> Account:
        db_acc = Account(id=get_id("Account"), status=status, **kwargs)
        db.add(db_acc)
        db.commit()
        db.refresh(db_acc)
        return db_acc

    @staticmethod
    def get_accounts(db: Session) -> List[Account]:
        return db.query(Account).all()

    @staticmethod
    def get_account(db: Session, account_id: str) -> Optional[Account]:
        return db.query(Account).filter(Account.id == account_id).first()

    @staticmethod
    def update_account(db: Session, account_id: str, **kwargs) -> Optional[Account]:
        db_acc = db.query(Account).filter(Account.id == account_id).first()
        if db_acc:
            for key, value in kwargs.items():
                setattr(db_acc, key, value)
            db.commit()
            db.refresh(db_acc)
        return db_acc

    @staticmethod
    def delete_account(db: Session, account_id: str) -> bool:
        db_acc = db.query(Account).filter(Account.id == account_id).first()
        if db_acc:
            db.delete(db_acc)
            db.commit()
            return True
        return False

# END FILE

# FILE: app/services/campaign_service.py
from sqlalchemy.orm import Session
from ..models import Campaign
from ..utils.sf_id import get_id
from typing import List, Optional

class CampaignService:
    @staticmethod
    def create_campaign(db: Session, **kwargs) -> Campaign:
        db_cmp = Campaign(id=get_id("Campaign"), **kwargs)
        db.add(db_cmp)
        db.commit()
        db.refresh(db_cmp)
        return db_cmp

    @staticmethod
    def get_campaigns(db: Session) -> List[Campaign]:
        return db.query(Campaign).all()

    @staticmethod
    def get_campaign(db: Session, campaign_id: str) -> Optional[Campaign]:
        return db.query(Campaign).filter(Campaign.id == campaign_id).first()

# END FILE

# FILE: app/services/contact_service.py
from sqlalchemy.orm import Session
from ..models import Contact
from ..utils.sf_id import get_id
from typing import List, Optional

class ContactService:
    @staticmethod
    def create_contact(db: Session, **kwargs) -> Contact:
        db_contact = Contact(id=get_id("Contact"), **kwargs)
        db.add(db_contact)
        db.commit()
        db.refresh(db_contact)
        return db_contact

    @staticmethod
    def get_contacts(db: Session, account_id: Optional[str] = None) -> List[Contact]:
        query = db.query(Contact)
        if account_id:
            query = query.filter(Contact.account_id == account_id)
        return query.all()

    @staticmethod
    def get_contact(db: Session, contact_id: str) -> Optional[Contact]:
        return db.query(Contact).filter(Contact.id == contact_id).first()

    @staticmethod
    def update_contact(db: Session, contact_id: str, **kwargs) -> Optional[Contact]:
        db_contact = db.query(Contact).filter(Contact.id == contact_id).first()
        if db_contact:
            for key, value in kwargs.items():
                setattr(db_contact, key, value)
            db.commit()
            db.refresh(db_contact)
        return db_contact

    @staticmethod
    def delete_contact(db: Session, contact_id: str) -> bool:
        db_contact = db.query(Contact).filter(Contact.id == contact_id).first()
        if db_contact:
            db.delete(db_contact)
            db.commit()
            return True
        return False

# END FILE

# FILE: app/services/product_service.py
from sqlalchemy.orm import Session
from ..models import Product
from ..utils.sf_id import get_id
from typing import List, Optional

class ProductService:
    @staticmethod
    def create_product(db: Session, **kwargs) -> Product:
        db_prod = Product(id=get_id("Product"), **kwargs)
        db.add(db_prod)
        db.commit()
        db.refresh(db_prod)
        return db_prod

    @staticmethod
    def get_products(db: Session) -> List[Product]:
        return db.query(Product).all()

    @staticmethod
    def get_product(db: Session, product_id: str) -> Optional[Product]:
        return db.query(Product).filter(Product.id == product_id).first()

# END FILE

# FILE: app/services/asset_service.py
from sqlalchemy.orm import Session
from ..models import Asset
from ..utils.sf_id import get_id
from typing import List, Optional

class AssetService:
    @staticmethod
    def create_asset(db: Session, account_id: str, name: str, product_id: Optional[str] = None, **kwargs) -> Asset:
        db_asset = Asset(id=get_id("Asset"), account_id=account_id, name=name, product_id=product_id, **kwargs)
        db.add(db_asset)
        db.commit()
        db.refresh(db_asset)
        return db_asset

    @staticmethod
    def get_assets(db: Session, account_id: Optional[str] = None) -> List[Asset]:
        query = db.query(Asset)
        if account_id:
            query = query.filter(Asset.account_id == account_id)
        return query.all()

    @staticmethod
    def get_asset(db: Session, asset_id: str) -> Optional[Asset]:
        return db.query(Asset).filter(Asset.id == asset_id).first()

    @staticmethod
    def update_asset(db: Session, asset_id: str, **kwargs) -> Optional[Asset]:
        db_asset = db.query(Asset).filter(Asset.id == asset_id).first()
        if db_asset:
            for key, value in kwargs.items():
                setattr(db_asset, key, value)
            db.commit()
            db.refresh(db_asset)
        return db_asset

    @staticmethod
    def delete_asset(db: Session, asset_id: str) -> bool:
        db_asset = db.query(Asset).filter(Asset.id == asset_id).first()
        if db_asset:
            db.delete(db_asset)
            db.commit()
            return True
        return False

# END FILE

# FILE: app/services/seed_service.py
import json
import httpx
import logging
from .ai_service import AIService, GROQ_API_KEY
from sqlalchemy.orm import Session

class SeedService:
    @staticmethod
    async def generate_theme_data(db: Session, theme: str, count: int = 5):
        """
        Generates realistic Automotive CRM data (Leads, Products, Accounts) using AI.
        """
        prompt = f"""
        Generate {count} realistic CRM entries for an Automotive business themed around '{theme}'.
        
        CRITICAL: Do NOT use real world car brands (No Hyundai, Tesla, etc.). 
        Use fictional high-end sounding brands like "Solaris", "Zenith", "Aeri", "Nebula".
        
        Generate:
        1. "leads": list of (first_name, last_name, company, email, phone, status: 'Open', 'Working', 'Nurturing')
        2. "products": list of (name: Car Model like 'Zenith S1', brand, category: 'EV', 'SUV', 'Sedan', base_price: integer, status: 'Active')
        3. "accounts": list of (name, industry: 'Automotive', record_type: 'Individual' or 'Corporate', tier: 'Bronze', 'Silver', 'Gold', status: 'Active')
        
        Return ONLY valid JSON with keys "leads", "products", "accounts".
        """
        
        api_key = GROQ_API_KEY
        base_url = "https://api.groq.com/openai/v1/chat/completions"
        model = "llama-3.3-70b-versatile"
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    base_url,
                    headers={"Authorization": f"Bearer {api_key}"},
                    json={
                        "model": model,
                        "messages": [{"role": "user", "content": prompt}],
                        "response_format": {"type": "json_object"}
                    },
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    raw_json = response.json()["choices"][0]["message"]["content"]
                    data = json.loads(raw_json)
                    
                    # 1. Seed Products
                    from .product_service import ProductService
                    for p in data.get("products", []):
                        ProductService.create_product(db, **p)
                        
                    # 2. Seed Leads
                    from .lead_service import LeadService
                    for l in data.get("leads", []):
                        LeadService.create_lead(db, **l)
                        
                    # 3. Seed Accounts
                    from .account_service import AccountService
                    for a in data.get("accounts", []):
                        AccountService.create_account(db, **a)
                        
                    return True
            except Exception as e:
                logging.error(f"Seeding failed: {e}")
                return False
        return False

# END FILE

# FILE: app/services/import_service.py
import csv
import io
from sqlalchemy.orm import Session
from .account_service import AccountService
from .contact_service import ContactService
from .lead_service import LeadService
from .opportunity_service import OpportunityService

class ImportService:
    @staticmethod
    async def import_csv(db: Session, object_type: str, file_content: str):
        f = io.StringIO(file_content)
        reader = csv.DictReader(f)
        imported_count = 0
        
        for row in reader:
            try:
                if object_type == "Account":
                    AccountService.create_account(db, **row)
                elif object_type == "Contact":
                    ContactService.create_contact(db, **row)
                elif object_type == "Lead":
                    LeadService.create_lead(db, **row)
                elif object_type == "Opportunity":
                    # Opportunity requires account_id
                    AccountService.create_account(db, **row)
                imported_count += 1
            except Exception as e:
                print(f"Error importing row: {e}")
        
        return imported_count

# END FILE

# FILE: docs/agent.md
# Automotive CRM Agent Definition

## Identity
- **Name**: Antigravity Automotive CRM Specialist
- **Mission**: To build a premium, Salesforce-aligned Automotive CRM (AutoCRM) specializing in Account/Contact/Asset/Product mapping for the vehicle industry.
- **Tone**: Professional, proactive, and meticulous about code quality.

## Core Rules
1. **Atomics First**: Every module, button, and function must be atomic.
2. **Phase Management**: Increment phase numbers for every major execution and documentation cycle.
3. **Backup Policy**: Consolidate EVERY file in the project (including `implementation_plan.md`) into `backups/module_phaseN.py` (naming suffix style) after every phase. No file should be left un-backed up.
4. **Validation**: Unit tests are mandatory for all core services before moving to the next phase. Always run unit tests before deployment and notify the user of results.
5. **Transparency**: Always request user confirmation with a detailed `implementation_plan.md` before execution.
6. **Absolute MD Rules**: The rules defined in `.md` files (agent, skill, blueprint, spec, workflow, task) are absolute. If a user prompt contradicts these documented rules, the user must be notified immediately.

## Strategy
- **Salesforce Benchmarking (Pixel-Perfect)**: Align the CRM UI layout (Tabs, Sidebar, Activity Feed) directly with the industry-standard Salesforce "Lightning" interface.
- **Lead Conversion Logic**: Implement the standard Salesforce workflow: Converting a Lead into a Person Account and an Opportunity without data loss.
- **Automotive Data Domain**: Specialize in Vehicle Assets, Car Model Products, and Dealership-specific stages.
- **Reporting Engine**: Build atomic services for data aggregation to support "Salesforce-like" dashboards.
- **Developer Flow**: Maintain a "Zero-Friction" setup with terminal-to-browser automation tools.

# END FILE

# FILE: docs/workflow.md
# Orchestration Workflow

## Phase-Based Execution Sequence
Every development phase must follow this strict sequence to ensure quality and traceability:

### 1. Planning Phase
- **Update `task.md`**: Define specific goals.
- **Implementation Plan**: Create/update `implementation_plan.md` for *every* phase.
- **Review `blueprint.md`**: Ensure design aligns with architecture.
- **Consult `spec.md`**: Define what success looks like for the new feature.

### 2. Execution Phase
- **Atomic Implementation**: Code changes in small, logical chunks (Models -> Services -> Routes -> UI).
- **Proactive Documentation**: Update relevant documentation as the code evolves.

### 3. Verification Phase
- **Unit Testing**: Run `pytest` for all core services.
- **Manual Verification**: Test UI flows (Modals, Buttons, Forms).
- **Quality Assurance**: Check for Salesforce-style validation and aesthetics.

### 4. Completion Phase
- **Walkthrough Generation**: Create/update `walkthrough_phaseX.md` for *every* phase to document proof of work and results.
- **Global Backup**: Run `backups/global_backup.py` with the appropriate Phase label. Every phase MUST have a corresponding backup.
- **User Notification**: Inform the user of completion and request feedback.

# END FILE

# FILE: docs/skill.md
# CRM Technical Skills

## 1. Database Mastery (SQLite + SQLAlchemy)
- Atomic CRUD operations.
- Schema migration safety.
- Relationship mapping for Messages and Contacts.

## 6. Governance & Compliance
- **MD Rule Adherence**: Ensuring every code change and interaction follows the absolute rules defined in the project's documentation.
- **Conflict Resolution**: Identifying and flags contradictions between user requests and established documentation.

## 2. Salesforce UI Alignment (Layout & UX)
- Pixel-perfect tab navigation and sidebar layouts.
- Component-based dashboard design (Quarterly Performance, Recent Records).
- Responsive "Lightning-like" interface using Vanilla CSS.

## 3. AI Data Generation (Theme-based Seeding)
- Dynamic synthesizing of realistic CRM data based on business themes.
- Validating and importing AI-generated JSON into SQLite.

## 3. Messaging Integration (SureM)
- SMS API handling.
- Asynchronous message status tracking.
- Provider-specific formatting and validation.

## 4. AI Orchestration (Groq + Cerebras)
- Real-time summarization skills.
- Sentiment analysis for descriptions.
- Automated summary generation for rapid lead assessment.

## 5. Verification & Reliability
- Pytest-driven development.
- Phase-based walkthrough generation.
- Automated backup procedures.
- Unit testing before deployment and user notification.

# END FILE

# FILE: docs/plan.md
# CRM Development Plan (Overall)

This document outlines the phased development of the CRM system with integrated messaging.

## Phases

### [Phase 1: Foundation & Core CRM Data]
- Project Structure setup.
- Environment configuration (.env).
- Database Schema design (SQLite).
- Atomic CRUD operations for Contacts.
- Implementation backup: `backups/crm_phase1.py`.

### [Phase 2: CRM Web Interface]
- Modern, premium UI construction.
- Contact dashboard and management tools.
- Validation and state management.

### [Phase 3: Messaging Integration]
- SureM API integration for SMS.
- Message history tracking.
- Automation and follow-up triggers.

### [Phase 4: Optimization & Polish]
- UX refinements.
- Final testing and documentation.

## Documentation Management
- `docs/agent`: Strategy and design documents.
- `docs/skill`: Implementation guides and specialized modules.
- `backups/`: Code snapshots for each phase.

# END FILE

# FILE: docs/spec.md
# Verification Spec

## Definition of Success
A feature is considered "Done" only when:
1. All core functionality requirements are met.
2. UI matches Salesforce design aesthetics (Modals, spacing, colors).
3. **Tabs**: Every record detail page must have visible and functional `Details` and `Related` tabs.
4. Unit tests pass (No regressions).
5. Phase backup is successfully executed.

## Test Checklist
- [ ] **ID Integrity**: Every new record must have a valid 18-character Salesforce-style ID.
- [ ] **Timestamp Auditing**: `CreatedDate` and `LastModifiedDate` must be automatically populated and non-editable via UI.
- [ ] **Validation**: Required fields must trigger a red banner/border error instead of a server crash.
- [ ] **Lead Lifecycle**: Converting a Lead must create an Account, Contact, and Opportunity with inherited Brand/Model interests.
- [ ] **Import Logic**: CSV files must be processed without duplicate IDs or blank essential fields.

## Edge Cases to Verify
- Null lookup values (e.g., Lead without a Campaign).
- Duplicate VINs in Assets (Must trigger a clean error).
- Partial CSV imports (Transaction atomicity).

# END FILE

# FILE: docs/blueprint.md
# System Blueprint

## Technical Stack
- **Framework**: FastAPI (Python 3.12+)
- **ORM**: SQLAlchemy 2.0+ (Declarative Mapping)
- **Database**: SQLite (Local file-based)
- **Frontend**: Jinja2 Templates + Vanilla CSS (Salesforce Lightning Design System inspiration)
- **AI Integration**: Groq/Cerebras (Llama 3 / 70B models)
- **Testing**: Pytest

## Architecture Overview
The system follows a modular Service-Oriented Architecture (SOA):
1. **Models (`models.py`)**: Defines Salesforce-aligned objects with 18-digit IDs and auto-timestamps.
2. **Services (`app/services/`)**: Contains atomic business logic (Lead conversion, data seeder, etc.).
3. **API Routes (`app/api/web_router.py`)**: Handles HTTP requests and template rendering.
4. **Utilities (`app/utils/`)**: Reusable logic like Salesforce ID generation (`sf_id.py`).

## UI Architecture (Detail Views)
- **Tabbed Interface**: Every detail page must implement a Salesforce-style tabbed UI.
- **Mandatory Tabs**: `Details` (Field-level data) and `Related` (Child record lists) are mandatory for all objects.
- **Path Component**: Leads and Opportunities must display a visual progress path (Status bar).
- **Two-Column Layout**: Detail fields should be presented in a responsive two-column grid.

## Data Flow
1. **Request Intake**: FastAPI router receives user interaction (e.g., Lead Conversion).
2. **Logic Execution**: Router delegates to the appropriate Service (e.g., `LeadService.convert_lead`).
3. **Database Mutation**: SQLAlchemy ORM commits changes to `crm.db`.
4. **UI Update**: Router returns a `RedirectResponse` or `TemplateResponse` to refresh the modal or list view.

# END FILE

# FILE: /Users/sangyeol.park@gruve.ai/.gemini/antigravity/brain/6fbb9986-03d2-4a1c-af1a-0cf7147cfd54/implementation_plan.md
# Implementation Plan - Phase 16: Interactive Detail Page & Advanced UI (Atomic CRUD)

Refine the Detail View to match high-fidelity Salesforce screenshots and fix foundational CRUD bugs (New button).

## User Review Required
> [!IMPORTANT]
> **Atomic CRUD**: I will ensure all service methods and routes are modular (atomic), making debugging and expansion easier.
> **Flow Field**: A new 'Flow' field will be added to Leads and Opportunities.

## Proposed Changes

### [Fixes]
#### [MODIFY] [web_router.py](file:///Users/sangyeol.park@gruve.ai/D4/app/api/web_router.py)
- Ensure all `list_` routes pass `plural_type` to the template.
- Ensure all `new_modal` routes are consistent.

### [Models & Services]
#### [MODIFY] [models.py](file:///Users/sangyeol.park@gruve.ai/D4/app/models.py)
- Add `is_flow_enabled = Column(Boolean, default=False)` to `Lead` and `Opportunity`.
- Ensure `created_at` and `updated_at` are present on all models (via `BaseModel`).

#### [Refactor] [LeadService](file:///Users/sangyeol.park@gruve.ai/D4/app/services/lead_service.py) & [OpportunityService](file:///Users/sangyeol.park@gruve.ai/D4/app/services/opportunity_service.py)
- Add `update_stage(db, id, stage)` atomic method.
- Add `toggle_flow(db, id, enabled)` atomic method.

### [Web Router & API]
#### [NEW] [web_router.py](file:///Users/sangyeol.park@gruve.ai/D4/app/api/web_router.py)
- `POST /leads/{id}/stage` - Update lead stage and return success.
- `POST /opportunities/{id}/stage` - Update opportunity stage and return success.
- `POST /leads/{id}/toggle-flow` - Toggle flow status.

### [Frontend & Templates]
#### [MODIFY] [style.css](file:///Users/sangyeol.park@gruve.ai/D4/app/static/css/style.css)
- Add styles for clickable path items with hover states.
- Add `.sf-system-info` for Created/Modified By layout.
- Add `.sf-description-large` for full-width text areas.
- Add `.sf-section-divider` for visual field grouping.

#### [MODIFY] [detail_view.html](file:///Users/sangyeol.park@gruve.ai/D4/app/templates/detail_view.html)
- Updated Path: Add `onclick` to call `updateStage(this, '{{plural_type}}', '{{record_id}}', '{{step.label}}')`.
- Header: Add dynamic "Flow" button (Primary when active).
- Body:
    - Group fields with dividers.
    - Large "Description" section at the bottom.
    - System Information section at the bottom with profile icons.

## Verification Plan
### Manual Verification
- Click a different stage in the Lead/Opportunity path and verify the "Detail" tab updates without a full page reload (or via quick refresh).
- Click the "Flow" button and verify the flow status changes.
- Verify the "Description" field spans the full width.
- Check "Created By" and "Last Modified By" look exactly like the screenshot.

# END FILE
