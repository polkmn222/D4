from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from ...database import get_db
from ...services.asset_service import AssetService
from ...services.contact_service import ContactService
from ...services.product_service import ProductService
from ...services.model_service import ModelService
from ...services.vehicle_spec_service import VehicleSpecService as BrandService
from ...core.templates import templates
from ...core.templates import templates
import logging

from ...core.toggles import is_feature_enabled

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/assets/{asset_id}")
async def asset_detail(request: Request, asset_id: str, db: Session = Depends(get_db)):
    if not is_feature_enabled("assets"):
        return RedirectResponse(url="/?error=Coming+Soon")
    try:
        logger.info(f"Accessing Asset Detail: {asset_id}")
        asset = AssetService.get_asset(db, asset_id)
        if not asset: return RedirectResponse(url="/assets?error=Asset+not+found")
        
        contact = ContactService.get_contact(db, asset.contact) if asset.contact else None
        prod = ProductService.get_product(db, asset.product) if asset.product else None
        model = ModelService.get_model(db, asset.model) if asset.model else None
        
        brand = BrandService.get_vehicle_spec(db, asset.brand) if asset.brand else (BrandService.get_vehicle_spec(db, model.brand) if (model and model.brand) else None)
        
        details = {
            "Name": asset.name if asset.name else "",
            "VIN": asset.vin if asset.vin else "",
            "Status": asset.status if asset.status else "",
            "Price": asset.price if asset.price else 0,
            "Contact": f"{contact.first_name} {contact.last_name}" if contact else (contact.name if contact else ""),
            "Contact_Hidden_Ref": asset.contact if asset.contact else "",
            "Brand": brand.name if brand else "",
            "Brand_Hidden_Ref": brand.id if brand else "",
            "Model": model.name if model else "",
            "Model_Hidden_Ref": asset.model if asset.model else "",
            "Product": prod.name if prod else "",
            "Product_Hidden_Ref": asset.product if asset.product else ""
        }
        return templates.TemplateResponse("detail_view.html", {
            "request": request, "object_type": "Asset", "plural_type": "assets",
            "record_id": asset_id, "record_name": asset.name if asset.name else "",
            "details": details, "created_at": asset.created_at, "updated_at": asset.updated_at,
            "related_lists": []
        })
    except Exception as e:
        logger.error(f"Error loading asset detail: {e}")
        return RedirectResponse(url=f"/assets?error=Error+loading+asset+detail:+{str(e).replace(' ', '+')}")

@router.get("/assets")
async def list_assets(request: Request, db: Session = Depends(get_db)):
    if not is_feature_enabled("assets"):
        return RedirectResponse(url="/?error=Coming+Soon")
    try:
        assets = AssetService.get_assets(db)
        items = []
        for a in assets:
            items.append({
                "id": a.id,
                "name": a.name if a.name else "",
                "vin": a.vin if a.vin else "",
                "price": a.price if a.price else 0,
                "status": a.status if a.status else "",
                "edit_url": f"/assets/new-modal?id={a.id}"
            })
        columns = ["name", "vin", "price", "status"]
        return templates.TemplateResponse("list_view.html", {
            "request": request, 
            "object_type": "Asset", 
            "plural_type": "assets",
            "items": items, 
            "columns": columns
        })
    except Exception as e:
        logger.error(f"Error listing assets: {e}")
        return RedirectResponse(url="/?error=Error+loading+assets")

@router.post("/assets/{asset_id}")
async def update_asset_endpoint(
    asset_id: str,
    name: str = Form(...),
    contact_id: str = Form(None),
    product_id: str = Form(None),
    brand_id: str = Form(None),
    model_id: str = Form(None),
    vin: str = Form(None),
    price: int = Form(0),
    status: str = Form("Active"),
    db: Session = Depends(get_db)
):
    try:
        AssetService.update_asset(
            db, asset_id, name=name, contact_id=contact_id, product_id=product_id, 
            brand_id=brand_id, model_id=model_id, vin=vin, price=price, status=status
        )
        return RedirectResponse(url=f"/assets/{asset_id}?success=Record+updated+successfully", status_code=303)
    except Exception as e:
        logger.error(f"Error updating asset: {e}")
        return RedirectResponse(url=f"/assets/{asset_id}?error=Error+updating+record")

@router.post("/assets/{asset_id}/delete")
async def delete_asset(request: Request, asset_id: str, db: Session = Depends(get_db)):
    AssetService.delete_asset(db, asset_id)
    if request.headers.get("Accept") == "application/json":
        return {"status": "success", "message": "Record deleted"}
    return RedirectResponse(url="/assets?success=Deleted", status_code=303)

@router.post("/assets")
async def create_asset_endpoint(
    name: str = Form(...),
    contact: str = Form(None),
    product: str = Form(None),
    brand: str = Form(None),
    model: str = Form(None),
    vin: str = Form(None),
    price: int = Form(0),
    status: str = Form("Active"),
    db: Session = Depends(get_db)
):
    try:
        asset = AssetService.create_asset(
            db, name=name, contact=contact, product=product, 
            brand=brand, model=model, vin=vin, price=price, status=status
        )
        return RedirectResponse(url=f"/assets/{asset.id}?success=Record+created+successfully", status_code=303)
    except Exception as e:
        logger.error(f"Error creating asset: {e}")
        return RedirectResponse(url="/assets?error=Error+creating+record")
