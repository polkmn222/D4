from fastapi import APIRouter, Request, Depends
from sqlalchemy.orm import Session
import logging

from ..database import get_db
from ..services.contact_service import ContactService
from ..services.lead_service import LeadService
from ..services.account_service import AccountService
from ..services.product_service import ProductService
from ..services.opportunity_service import OpportunityService
from ..services.asset_service import AssetService
from ..services.campaign_service import CampaignService
from ..services.vehicle_spec_service import VehicleSpecService as BrandService
from ..services.model_service import ModelService
from ..services.task_service import TaskService
from ..services.message_service import MessageService
from ..services.message_template_service import MessageTemplateService
from ..core.templates import templates

logger = logging.getLogger(__name__)
router = APIRouter()

# Alias for backward compatibility if needed, but we'll use BrandService consistently
VehicleSpecificationService = BrandService

# --- CONTACTS ---
@router.get("/contacts/new")
async def new_contact_modal(request: Request, id: str = None, db: Session = Depends(get_db)):
    fields = ["first_name", "last_name", "email", "phone", "account"]
    initial_values = None
    if id:
        contact = ContactService.get_contact(db, id)
        if contact:
            acc = AccountService.get_account(db, contact.account) if contact.account else None
            initial_values = {
                "id": contact.id,
                "first_name": contact.first_name,
                "last_name": contact.last_name,
                "email": contact.email,
                "phone": contact.phone,
                "account": contact.account,
                "account_name": acc.name if acc else ""
            }
    return templates.TemplateResponse("templates/sf_form_modal.html", {
        "request": request, "object_type": "Contact", "plural_type": "contacts",
        "fields": fields, "initial_values": initial_values
    })

# --- LEADS ---
@router.get("/leads/{lead_id}/convert-modal")
async def lead_convert_modal(request: Request, lead_id: str, db: Session = Depends(get_db)):
    from backend.app.services.lead_service import LeadService
    lead = LeadService.get_lead(db, lead_id)
    if not lead:
        return {"status": "error", "message": "Lead not found"}
    return templates.TemplateResponse("leads/lead_convert_modal.html", {
        "request": request, "lead": lead
    })

@router.get("/leads/new")
async def new_lead_modal(request: Request, id: str = None, db: Session = Depends(get_db)):
    brands = VehicleSpecificationService.get_vehicle_specs(db, record_type="Brand")
    models = ["TBD"] # Placeholder or fetch from ModelService
    fields = ["first_name", "last_name", "email", "phone", "status", "gender", "brand", "model", "product", "description"]
    initial_values = None
    if id:
        lead = LeadService.get_lead(db, id)
        if lead:
            brand = BrandService.get_vehicle_spec(db, lead.brand) if lead.brand else None
            model = ModelService.get_model(db, lead.model) if lead.model else None
            prod = ProductService.get_product(db, lead.product) if lead.product else None
            initial_values = {
                "id": lead.id, "first_name": lead.first_name, "last_name": lead.last_name,
                "email": lead.email, "phone": lead.phone, "status": lead.status,
                "gender": lead.gender, "brand": lead.brand, "brand_name": brand.name if brand else "",
                "model": lead.model, "model_name": model.name if model else "",
                "product": lead.product, "product_name": prod.name if prod else "",
                "description": lead.description
            }
    return templates.TemplateResponse("templates/sf_form_modal.html", {
        "request": request, "object_type": "Lead", "plural_type": "leads",
        "brands": brands, "models": models, "fields": fields, "initial_values": initial_values
    })

# --- ACCOUNTS ---
@router.get("/accounts/record_type")
async def account_record_type(request: Request):
    return templates.TemplateResponse("accounts/account_record_type.html", {"request": request})

@router.get("/accounts/new-modal")
async def new_account_modal_base(request: Request, type: str = "Individual", id: str = None, db: Session = Depends(get_db)):
    return await new_account_modal(request, type, id, db)

@router.get("/accounts/new")
async def new_account_modal(request: Request, type: str = "Individual", id: str = None, db: Session = Depends(get_db)):
    fields = ["name", "phone", "email", "industry", "website", "status", "description"]
    initial_values = None
    if id:
        acc = AccountService.get_account(db, id)
        if acc:
            initial_values = {
                "id": acc.id, "name": acc.name, "phone": acc.phone, "email": acc.email,
                "industry": acc.industry, "website": acc.website, "status": acc.status,
                "description": acc.description
            }
            type = acc.record_type
    return templates.TemplateResponse("templates/sf_form_modal.html", {
        "request": request, "object_type": "Account", "plural_type": "accounts",
        "record_type": type, "fields": fields, "initial_values": initial_values
    })

# --- OPPORTUNITIES ---
@router.get("/opportunities/new-modal")
async def new_opportunity_modal_base(request: Request, id: str = None, db: Session = Depends(get_db)):
    return await new_opportunity_modal(request, id, db)

@router.get("/opportunities/new")
async def new_opportunity_modal(request: Request, id: str = None, db: Session = Depends(get_db)):
    fields = ["account", "name", "amount", "stage", "status", "brand", "model", "product", "asset", "probability"]
    initial_values = None
    if id:
        opp = OpportunityService.get_opportunity(db, id)
        if opp:
            acc = AccountService.get_account(db, opp.account) if opp.account else None
            brand = VehicleSpecificationService.get_vehicle_spec(db, opp.brand) if opp.brand else None
            model = ModelService.get_model(db, opp.model) if opp.model else None
            prod = ProductService.get_product(db, opp.product) if opp.product else None
            asset = AssetService.get_asset(db, opp.asset) if opp.asset else None
            initial_values = {
                "id": opp.id, "account": opp.account, "account_name": acc.name if acc else "",
                "name": opp.name, "amount": opp.amount, "stage": opp.stage, "status": opp.status,
                "brand": opp.brand, "brand_name": brand.name if brand else "",
                "model": opp.model, "model_name": model.name if model else "",
                "product": opp.product, "product_name": prod.name if prod else "",
                "asset": opp.asset, "asset_name": asset.name if asset else "",
                "probability": opp.probability
            }
    return templates.TemplateResponse("templates/sf_form_modal.html", {
        "request": request, "object_type": "Opportunity", "plural_type": "opportunities",
        "fields": fields, "initial_values": initial_values
    })

# --- VEHICLE SPECIFICATIONS ---
@router.get("/vehicle_specifications/record_type")
async def spec_record_type(request: Request):
    return templates.TemplateResponse("brands/spec_record_type.html", {"request": request})

@router.get("/vehicle_specifications/new-modal")
async def new_spec_modal_base(request: Request, type: str = "Brand", id: str = None, db: Session = Depends(get_db)):
    return await new_spec_modal(request, type, id, db)

@router.get("/vehicle_specifications/new")
async def new_spec_modal(request: Request, type: str = "Brand", id: str = None, db: Session = Depends(get_db)):
    fields = ["name", "description"]
    if type == "Model":
        fields.append("parent")
    
    initial_values = None
    if id:
        spec = VehicleSpecificationService.get_vehicle_spec(db, id)
        if spec:
            parent = BrandService.get_vehicle_spec(db, spec.parent) if spec.parent else None
            initial_values = {
                "id": spec.id, "name": spec.name, "description": spec.description, 
                "parent": spec.parent, "brand_name": parent.name if parent else ""
            }
            type = spec.record_type
            if type == "Model" and "parent" not in fields:
                fields.append("parent")
                
    return templates.TemplateResponse("templates/sf_form_modal.html", {
        "request": request, "object_type": "VehicleSpecification", "plural_type": "vehicle_specifications",
        "record_type": type, "fields": fields, "initial_values": initial_values
    })

# --- MODELS ---
from ..services.model_service import ModelService

@router.get("/models/new-modal")
async def new_model_modal_base(request: Request, id: str = None, db: Session = Depends(get_db)):
    return await new_model_modal(request, id, db)

@router.get("/models/new")
async def new_model_modal(request: Request, id: str = None, db: Session = Depends(get_db)):
    fields = ["name", "brand", "description"]
    initial_values = None
    if id:
        model = ModelService.get_model(db, id)
        if model:
            brand = BrandService.get_vehicle_spec(db, model.brand) if model.brand else None
            initial_values = {
                "id": model.id, "name": model.name, "description": model.description,
                "brand": model.brand, "brand_name": brand.name if brand else ""
            }
    return templates.TemplateResponse("templates/sf_form_modal.html", {
        "request": request, "object_type": "Model", "plural_type": "models",
        "fields": fields, "initial_values": initial_values
    })

# --- CAMPAIGNS ---
@router.get("/campaigns/new-modal")
async def new_campaign_modal_base(request: Request, id: str = None, db: Session = Depends(get_db)):
    return await new_campaign_modal(request, id, db)

@router.get("/campaigns/new")
async def new_campaign_modal(request: Request, id: str = None, db: Session = Depends(get_db)):
    fields = ["name", "type", "status", "description"] # Skipping dates for simplicity in standard input
    initial_values = None
    if id:
        cmp = CampaignService.get_campaign(db, id)
        if cmp:
            initial_values = {
                "id": cmp.id, "name": cmp.name, "type": cmp.type,
                "status": cmp.status, "description": cmp.description
            }
    return templates.TemplateResponse("templates/sf_form_modal.html", {
        "request": request, "object_type": "Campaign", "plural_type": "campaigns",
        "fields": fields, "initial_values": initial_values
    })

# --- PRODUCTS ---
@router.get("/products/new-modal")
async def new_product_modal_base(request: Request, id: str = None, db: Session = Depends(get_db)):
    return await new_product_modal(request, id, db)

@router.get("/products/new")
async def new_product_modal(request: Request, id: str = None, db: Session = Depends(get_db)):
    fields = ["name", "brand", "model", "category", "base_price", "description"]
    initial_values = None
    if id:
        prod = ProductService.get_product(db, id)
        if prod:
            brand = BrandService.get_vehicle_spec(db, prod.brand) if prod.brand else None
            model = ModelService.get_model(db, prod.model) if prod.model else None
            initial_values = {
                "id": prod.id, "name": prod.name, 
                "brand": prod.brand, "brand_name": brand.name if brand else "",
                "model": prod.model, "model_name": model.name if model else "",
                "category": prod.category, "base_price": prod.base_price, "description": prod.description
            }
    return templates.TemplateResponse("templates/sf_form_modal.html", {
        "request": request, "object_type": "Product", "plural_type": "products",
        "fields": fields, "initial_values": initial_values
    })

# --- ASSETS ---
@router.get("/assets/new-modal")
async def new_asset_modal_base(request: Request, id: str = None, db: Session = Depends(get_db)):
    return await new_asset_modal(request, id, db)

@router.get("/assets/new")
async def new_asset_modal(request: Request, id: str = None, db: Session = Depends(get_db)):
    fields = ["account", "product", "brand", "model", "name", "vin", "status", "price"]
    initial_values = None
    if id:
        asset = AssetService.get_asset(db, id)
        if asset:
            acc = AccountService.get_account(db, asset.account) if asset.account else None
            prod = ProductService.get_product(db, asset.product) if asset.product else None
            brand = BrandService.get_vehicle_spec(db, asset.brand) if asset.brand else None
            model = ModelService.get_model(db, asset.model) if asset.model else None
            initial_values = {
                "id": asset.id, "account": asset.account, "account_name": acc.name if acc else "",
                "product": asset.product, "product_name": prod.name if prod else "",
                "brand": asset.brand, "brand_name": brand.name if brand else "",
                "model": asset.model, "model_name": model.name if model else "",
                "name": asset.name, "vin": asset.vin, "status": asset.status, "price": asset.price
            }
    return templates.TemplateResponse("templates/sf_form_modal.html", {
        "request": request, "object_type": "Asset", "plural_type": "assets",
        "fields": fields, "initial_values": initial_values
    })

# --- TASKS ---
@router.get("/tasks/new-modal")
async def new_task_modal_base(request: Request, id: str = None, db: Session = Depends(get_db)):
    return await new_task_modal(request, id, db)

@router.get("/tasks/new")
async def new_task_modal(request: Request, id: str = None, db: Session = Depends(get_db)):
    fields = ["subject", "status", "priority", "account", "opportunity", "message", "description"]
    initial_values = None
    if id:
        task = TaskService.get_task(db, id)
        if task:
            acc = AccountService.get_account(db, task.account) if task.account else None
            opp = OpportunityService.get_opportunity(db, task.opportunity) if task.opportunity else None
            msg = MessageService.get_message(db, task.message) if task.message else None
            initial_values = {
                "id": task.id, "subject": task.subject, "status": task.status, "priority": task.priority,
                "account": task.account, "account_name": acc.name if acc else "",
                "opportunity": task.opportunity, "opportunity_name": opp.name if opp else "",
                "message": task.message, "message_name": f"Message {task.message}" if msg else "",
                "description": task.description
            }
    return templates.TemplateResponse("templates/sf_form_modal.html", {
        "request": request, "object_type": "Task", "plural_type": "tasks",
        "fields": fields, "initial_values": initial_values
    })

# --- MESSAGES & TEMPLATES ---
@router.get("/messages/new-modal")
async def new_message_modal_base(request: Request, id: str = None, db: Session = Depends(get_db)):
    return await new_message_modal(request, id, db)

@router.get("/messages/new")
async def new_message_modal(request: Request, id: str = None, db: Session = Depends(get_db)):
    fields = ["contact", "account", "template", "direction", "content", "status"]
    initial_values = None
    if id:
        msg = MessageService.get_message(db, id)
        if msg:
            contact = ContactService.get_contact(db, msg.contact) if msg.contact else None
            acc = AccountService.get_account(db, msg.account) if msg.account else None
            template = MessageTemplateService.get_template(db, msg.template) if msg.template else None
            initial_values = {
                "id": msg.id, "contact": msg.contact, "contact_name": f"{contact.first_name} {contact.last_name}" if contact else "",
                "account": msg.account, "account_name": acc.name if acc else "",
                "template": msg.template, "template_name": template.name if template else "",
                "direction": msg.direction, "content": msg.content, "status": msg.status
            }
    return templates.TemplateResponse("templates/sf_form_modal.html", {
        "request": request, "object_type": "Message", "plural_type": "messages",
        "fields": fields, "initial_values": initial_values
    })

@router.get("/leads/new-modal")
async def new_lead_modal_base(request: Request, id: str = None, db: Session = Depends(get_db)):
    return await new_lead_modal(request, id, db)

@router.get("/leads/new")
async def new_lead_modal_direct(request: Request, id: str = None, db: Session = Depends(get_db)):
    return await new_lead_modal(request, id, db)

@router.get("/message_templates/new-modal")
async def new_template_modal_base(request: Request, id: str = None, db: Session = Depends(get_db)):
    return await new_template_modal(request, id, db)

@router.get("/message_templates/new")
async def new_template_modal(request: Request, id: str = None, db: Session = Depends(get_db)):
    fields = ["name", "record_type", "subject", "body"]
    initial_values = None
    if id:
        t = MessageTemplateService.get_template(db, id)
        if t:
            initial_values = {
                "id": t.id,
                "name": t.name,
                "record_type": t.record_type if hasattr(t, 'record_type') else "SMS",
                "subject": t.subject,
                "body": t.body
            }
    return templates.TemplateResponse("templates/sf_form_modal.html", {
        "request": request, "object_type": "MessageTemplate", "plural_type": "message_templates",
        "fields": fields, "initial_values": initial_values
    })

