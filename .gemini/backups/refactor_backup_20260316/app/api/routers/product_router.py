from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from ...database import get_db
from ...services.product_service import ProductService
from ...services.model_service import ModelService
from ...services.vehicle_spec_service import VehicleSpecService as BrandService
from ...services.vehicle_spec_service import VehicleSpecService as VehicleSpecificationService
from ...core.templates import templates
from ...models import Product
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/products/{product_id}")
async def product_detail(request: Request, product_id: str, db: Session = Depends(get_db)):
    try:
        logger.info(f"Accessing Product Detail: {product_id}")
        product = ProductService.get_product(db, product_id)
        if not product: return RedirectResponse(url="/products?error=Product+not+found")
        
        brand_spec = BrandService.get_vehicle_spec(db, product.brand_id) if product.brand_id else None
        model_spec = ModelService.get_model(db, product.model_id) if product.model_id else None
        
        details = {
            "Name": product.name if product.name else "N/A",
            "Brand": brand_spec.name if brand_spec else product.brand,
            "Brand_Hidden_Ref": product.brand_id,
            "Model": model_spec.name if model_spec else "N/A",
            "Model_Hidden_Ref": product.model_id,
            "Category": product.category,
            "Price": product.base_price if product.base_price else 0,
            "Description": product.description
        }
        return templates.TemplateResponse("detail_view.html", {
            "request": request, "object_type": "Product", "plural_type": "products",
            "record_id": product_id, "record_name": product.name if product.name else "N/A",
            "details": details, "created_at": product.created_at, "updated_at": product.updated_at,
            "related_lists": []
        })
    except Exception as e:
        logger.error(f"Error loading product detail: {e}")
        return RedirectResponse(url=f"/products?error=Error+loading+product+detail:+{str(e).replace(' ', '+')}")

@router.get("/products")
async def list_products(request: Request, db: Session = Depends(get_db)):
    try:
        products = ProductService.get_products(db)
        items = []
        for p in products:
            brand = VehicleSpecificationService.get_vehicle_spec(db, p.brand_id) if (hasattr(p, 'brand_id') and p.brand_id) else None
            model = ModelService.get_model(db, p.model_id) if (hasattr(p, 'model_id') and p.model_id) else None
            items.append({
                "id": p.id,
                "name": p.name,
                "brand": brand.name if brand else "",
                "model": model.name if model else "",
                "base_price": p.base_price if p.base_price else 0,
                "category": p.category if p.category else "",
                "edit_url": f"/products/new-modal?id={p.id}"
            })
        columns = ["name", "brand", "model", "base_price", "category"]
        return templates.TemplateResponse("list_view.html", {
            "request": request, 
            "object_type": "Product", 
            "plural_type": "products",
            "items": items, 
            "columns": columns
        })
    except Exception as e:
        logger.error(f"List products error: {e}")
        return RedirectResponse(url="/?error=Error+loading+products")

@router.post("/products")
async def create_product(
    name: str = Form(...),
    brand_id: str = Form(None),
    model_id: str = Form(None),
    category: str = Form(None),
    base_price: int = Form(0),
    description: str = Form(None),
    db: Session = Depends(get_db)
):
    try:
        product = ProductService.create_product(
            db, name=name, brand_id=brand_id, model_id=model_id, category=category, base_price=base_price, description=description
        )
        return RedirectResponse(url=f"/products/{product.id}?success=Product+created+successfully", status_code=303)
    except Exception as e:
        logger.error(f"Error creating product: {e}")
        return RedirectResponse(url="/products?error=Error+creating+product")

@router.post("/products/{product_id}")
async def update_product(
    product_id: str,
    name: str = Form(...),
    brand_id: str = Form(None),
    model_id: str = Form(None),
    category: str = Form(None),
    base_price: int = Form(0),
    description: str = Form(None),
    db: Session = Depends(get_db)
):
    try:
        ProductService.update_product(
            db, product_id, name=name, brand_id=brand_id, model_id=model_id, category=category, base_price=base_price, description=description
        )
        return RedirectResponse(url=f"/products/{product_id}?success=Product+updated+successfully", status_code=303)
    except Exception as e:
        logger.error(f"Error updating product: {e}")
        return RedirectResponse(url=f"/products/{product_id}?error=Error+updating+product")

@router.post("/products/{product_id}/delete")
async def delete_product(request: Request, product_id: str, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if product:
        db.delete(product)
        db.commit()
    if "application/json" in request.headers.get("Accept", ""):
        return {"status": "success", "message": "Record deleted successfully"}
    return RedirectResponse(url="/products?success=Record+deleted+successfully", status_code=303)
