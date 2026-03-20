from fastapi import APIRouter, Request, Depends, Form, UploadFile, File
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from ...database import get_db
from ...services.contact_service import ContactService
from ...services.lead_service import LeadService
from ...services.account_service import AccountService
from ...services.product_service import ProductService
from ...services.opportunity_service import OpportunityService
from ...services.asset_service import AssetService
from ...services.task_service import TaskService
from ...services.model_service import ModelService
from ...services.vehicle_spec_service import VehicleSpecService as VehicleSpecificationService
from ...services.import_service import ImportService
from ...services.campaign_service import CampaignService
from ... import models
from datetime import datetime
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/{object_type}/{record_id}/inline-save")
async def inline_save(object_type: str, record_id: str, field: str = Form(...), value: str = Form(...), db: Session = Depends(get_db)):
    field_name = field.lower().replace(" ", "_")
    
    object_type_map = {
        "leads": (LeadService, LeadService.get_lead),
        "opportunities": (OpportunityService, OpportunityService.get_opportunity),
        "accounts": (AccountService, AccountService.get_account),
        "contacts": (ContactService, ContactService.get_contact),
        "assets": (AssetService, AssetService.get_asset),
        "campaigns": (CampaignService, CampaignService.get_campaign),
        "products": (ProductService, ProductService.get_product),
        "vehicle_specifications": (VehicleSpecificationService, VehicleSpecificationService.get_vehicle_spec),
        "tasks": (TaskService, TaskService.get_task),
        "models": (ModelService, ModelService.get_model)
    }

    record_tuple = object_type_map.get(object_type)

    if not record_tuple:
        logger.error(f"Object type {object_type} not supported for inline save")
        return {"status": "error", "message": "Object type not supported"}
        
    service, get_method = record_tuple
    record = get_method(db, record_id)
    
    if record:
        field_norm = field_name.lower()
        if field_norm == "account_hidden_ref": update_data = {"account": value}
        elif field_norm == "brand_hidden_ref": update_data = {"brand": value}
        elif field_norm == "model_hidden_ref": update_data = {"model": value}
        elif field_norm == "product_hidden_ref": update_data = {"product": value}
        elif field_norm == "asset_hidden_ref": update_data = {"asset": value}
        elif field_norm == "opportunity_name": 
            update_data = {"name": value}
        elif field_norm == "name" and object_type in ["leads", "contacts"]:
            parts = value.split(" ", 1)
            first_name = parts[0]
            last_name = parts[1] if len(parts) > 1 else ""
            update_data = {"first_name": first_name, "last_name": last_name}
        else:
            update_data = {field_norm: value}

        service_update_func = None
        if object_type == "vehicle_specifications":
            service_update_func = service.update_vehicle_spec
        elif object_type == "opportunities":
            service_update_func = service.update_opportunity
        elif object_type == "leads":
            service_update_func = service.update_lead
        elif object_type == "accounts":
            service_update_func = service.update_account
        elif object_type == "contacts":
            service_update_func = service.update_contact
        elif object_type == "campaigns":
            service_update_func = service.update_campaign
        elif object_type == "products":
            service_update_func = service.update_product
        elif object_type == "tasks":
            service_update_func = service.update_task
        else:
            if object_type.endswith('ies'):
                singular_type = object_type[:-3] + 'y'
            elif object_type.endswith('s'):
                singular_type = object_type[:-1]
            else:
                singular_type = object_type
            service_update_func = getattr(service, f"update_{singular_type}", None)

        if service_update_func and update_data:
            service_update_func(db, record_id, **update_data)
            logger.info(f"Field {field_name} updated for {object_type} {record_id}")
            return {"status": "success", "field": field_name, "value": value}
        else:
            logger.error(f"Update function not found for object type {object_type}")
            return {"status": "error", "message": "Update function not found"}
    
    return {"status": "error", "message": "Record not found"}

@router.post("/import")
async def import_csv(
    object_type: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    content = await file.read()
    decoded = content.decode("utf-8")
    await ImportService.import_csv(db, object_type, decoded)
    return RedirectResponse(url=f"/{object_type.lower()}s", status_code=303)

@router.post("/seed")
async def seed_data(theme: str = Form(...), db: Session = Depends(get_db)):
    from ...services.seed_service import SeedService
    await SeedService.generate_theme_data(db, theme, count=5)
    return RedirectResponse(url="/", status_code=303)

@router.get("/lookups/search")
async def lookup_search(
    q: str = "",
    type: str = "Account",
    db: Session = Depends(get_db)
):
    results = []
    limit = 5
    
    if type == "Account":
        data = db.query(models.Account).filter(models.Account.name.ilike(f"%{q}%")).limit(limit).all()
        for item in data: results.append({"id": item.id, "name": item.name, "type": "Account"})
    elif type == "Contact":
        data = db.query(models.Contact).filter(
            (models.Contact.first_name + " " + models.Contact.last_name).ilike(f"%{q}%")
        ).limit(limit).all()
        for item in data: results.append({"id": item.id, "name": f"{item.first_name} {item.last_name}", "type": "Contact"})
    elif type == "Product":
        data = db.query(models.Product).filter(models.Product.name.ilike(f"%{q}%")).limit(limit).all()
        for item in data: results.append({"id": item.id, "name": item.name, "type": "Product"})
    elif type == "Asset":
        data = db.query(models.Asset).filter(models.Asset.name.ilike(f"%{q}%")).limit(limit).all()
        for item in data: results.append({"id": item.id, "name": item.name, "type": "Asset", "price": item.price})
    elif type == "VehicleSpecification" or type == "Brand":
        data = db.query(models.VehicleSpecification).filter(models.VehicleSpecification.name.ilike(f"%{q}%")).limit(limit).all()
        for item in data: results.append({"id": item.id, "name": item.name, "type": "Brand"})
    elif type == "Campaign":
        data = db.query(models.Campaign).filter(models.Campaign.name.ilike(f"%{q}%")).limit(limit).all()
        for item in data: results.append({"id": item.id, "name": item.name, "type": "Campaign"})
    elif type == "Model":
        data = db.query(models.Model).filter(models.Model.name.ilike(f"%{q}%")).limit(limit).all()
        for item in data: results.append({"id": item.id, "name": item.name, "type": "Model"})

    return {"results": results}
