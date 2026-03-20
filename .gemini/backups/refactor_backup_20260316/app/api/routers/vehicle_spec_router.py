from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from ...database import get_db
from ...services.vehicle_spec_service import VehicleSpecService as BrandService
from ...services.vehicle_spec_service import VehicleSpecService
from ...services.vehicle_spec_service import VehicleSpecService as VehicleSpecificationService
from ...services.model_service import ModelService
from ...models import VehicleSpecification
from ... import models
from ...core.templates import templates
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/vehicle_specifications/{spec_id}")
async def vehicle_spec_detail(request: Request, spec_id: str, db: Session = Depends(get_db)):
    logger.info(f"Accessing Vehicle Specification Detail: {spec_id}")
    spec = VehicleSpecificationService.get_vehicle_spec(db, spec_id)
    if not spec: return RedirectResponse(url="/vehicle_specifications")
    details = {
        "Name": spec.name,
        "Record_Type": spec.record_type,
        "Parent_Id": spec.parent_id
    }
    # Related Models
    from ...models import Model as ModelModel
    models_list = db.query(ModelModel).filter(ModelModel.brand_id == spec_id).all()
    related_lists = []
    if models_list:
        related_lists.append({
            "title": "Models",
            "columns": ["name", "description"],
            "items": [{"name": m.name, "description": m.description} for m in models_list]
        })

    return templates.TemplateResponse("detail_view.html", {
        "request": request, 
        "object_type": "Brand", 
        "plural_type": "vehicle_specifications",
        "record_id": spec_id,
        "record_name": spec.name,
        "details": details,
        "created_at": spec.created_at,
        "updated_at": spec.updated_at,
        "related_lists": related_lists
    })

@router.get("/vehicle_specifications")
async def list_specs(request: Request, db: Session = Depends(get_db)):
    specs = VehicleSpecificationService.get_vehicle_specs(db)
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
        "request": request, 
        "object_type": "Brand", 
        "plural_type": "vehicle_specifications",
        "items": items, 
        "columns": columns
    })

@router.post("/vehicle_specifications")
async def create_spec(
    name: str = Form(...),
    record_type: str = Form("Brand"),
    parent_id: str = Form(None),
    description: str = Form(None),
    db: Session = Depends(get_db)
):
    spec = VehicleSpecService.create_spec(
        db, name=name, record_type=record_type, parent_id=parent_id, description=description
    )
    return RedirectResponse(url=f"/vehicle_specifications/{spec.id}?success=Record+created+successfully", status_code=303)

@router.post("/vehicle_specifications/{spec_id}")
async def update_spec(
    spec_id: str,
    name: str = Form(...),
    record_type: str = Form("Brand"),
    parent_id: str = Form(None),
    description: str = Form(None),
    db: Session = Depends(get_db)
):
    spec = db.query(VehicleSpecification).filter(VehicleSpecification.id == spec_id).first()
    if spec:
        spec.name = name
        spec.record_type = record_type
        spec.parent_id = parent_id
        spec.description = description
        db.commit()
    return RedirectResponse(url=f"/vehicle_specifications/{spec_id}" + "?success=Record+updated+successfully", status_code=303)

@router.post("/vehicle_specifications/{spec_id}/delete")
async def delete_spec(request: Request, spec_id: str, db: Session = Depends(get_db)):
    VehicleSpecService.delete_vehicle_spec(db, spec_id)
    if "application/json" in request.headers.get("Accept", ""):
        return {"status": "success", "message": "Record deleted successfully"}
    return RedirectResponse(url="/vehicle_specifications?success=Record+deleted+successfully", status_code=303)

@router.post("/vehicle_specifications/{spec_id}/restore")
async def restore_spec_endpoint(spec_id: str, db: Session = Depends(get_db)):
    spec = db.query(models.VehicleSpecification).filter(models.VehicleSpecification.id == spec_id).first()
    if spec:
        spec.deleted_at = None
        db.commit()
    return {"status": "success"}

# --- MODELS ---
@router.get("/models/{model_id}")
async def model_detail(request: Request, model_id: str, db: Session = Depends(get_db)):
    try:
        logger.info(f"Accessing Model Detail: {model_id}")
        model = ModelService.get_model(db, model_id)
        if not model: return RedirectResponse(url="/models?error=Model+not+found")
        
        brand = BrandService.get_vehicle_spec(db, model.brand_id) if model.brand_id else None
        
        details = {
            "Name": model.name,
            "Brand": brand.name if brand else None,
            "Brand_Hidden_Ref": model.brand_id,
            "Description": model.description
        }
        
        return templates.TemplateResponse("detail_view.html", {
            "request": request, "object_type": "Model", "plural_type": "models",
            "record_id": model_id, "record_name": model.name,
            "details": details, "created_at": model.created_at,
            "updated_at": model.updated_at, "related_lists": []
        })
    except Exception as e:
        logger.error(f"Error loading model detail: {e}")
        return RedirectResponse(url=f"/models?error=Error+loading+model+detail:+{str(e).replace(' ', '+')}")

@router.get("/models")
async def list_models(request: Request, db: Session = Depends(get_db)):
    models_data = ModelService.get_models(db)
    items = []
    for m in models_data:
        brand = BrandService.get_vehicle_spec(db, m.brand_id) if m.brand_id else None
        items.append({
            "id": m.id,
            "name": m.name,
            "brand": brand.name if brand else "",
            "description": m.description if m.description else "",
            "edit_url": f"/models/new-modal?id={m.id}"
        })
    columns = ["name", "brand", "description"]
    return templates.TemplateResponse("list_view.html", {
        "request": request, "object_type": "Model", "plural_type": "models",
        "items": items, "columns": columns
    })

@router.post("/models")
async def create_model_route(
    name: str = Form(...),
    brand_id: str = Form(None),
    description: str = Form(None),
    db: Session = Depends(get_db)
):
    try:
        model = ModelService.create_model(db, name=name, brand_id=brand_id, description=description)
        return RedirectResponse(url=f"/models/{model.id}?success=Record+created+successfully", status_code=303)
    except Exception as e:
        logger.error(f"Error creating model: {e}")
        return RedirectResponse(url="/models?error=Error+creating+model")

@router.post("/models/{model_id}")
async def update_model_route(
    model_id: str,
    name: str = Form(...),
    brand_id: str = Form(None),
    description: str = Form(None),
    db: Session = Depends(get_db)
):
    try:
        ModelService.update_model(db, model_id, name=name, brand_id=brand_id, description=description)
        return RedirectResponse(url=f"/models/{model_id}?success=Record+updated+successfully", status_code=303)
    except Exception as e:
        logger.error(f"Error updating model: {e}")
        return RedirectResponse(url=f"/models/{model_id}?error=Error+updating+model")

@router.post("/models/{model_id}/delete")
async def delete_model_route(request: Request, model_id: str, db: Session = Depends(get_db)):
    try:
        ModelService.delete_model(db, model_id)
        if "application/json" in request.headers.get("Accept", ""):
            return {"status": "success", "message": "Record deleted successfully"}
        return RedirectResponse(url="/models?success=Record+deleted+successfully", status_code=303)
    except Exception as e:
        logger.error(f"Error deleting model: {e}")
        return RedirectResponse(url=f"/models?error=Error+deleting+model")
