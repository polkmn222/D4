from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from ...database import get_db
from ...services.opportunity_service import OpportunityService
from ...services.account_service import AccountService
from ...services.product_service import ProductService
from ...services.asset_service import AssetService
from ...services.model_service import ModelService
from ...services.vehicle_spec_service import VehicleSpecService as BrandService
from ...core.templates import templates
from ... import models
from datetime import datetime
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/opportunities/{opp_id}")
async def opportunity_detail(request: Request, opp_id: str, db: Session = Depends(get_db)):
    try:
        logger.info(f"Accessing Opportunity Detail: {opp_id}")
        # track visit for history
        OpportunityService.update_last_viewed(db, opp_id)
        opp = OpportunityService.get_opportunity(db, opp_id)
        if not opp:
            return RedirectResponse(url="/opportunities?error=Opportunity+not+found")
        
        account = AccountService.get_account(db, opp.account_id) if opp.account_id else None
        product = ProductService.get_product(db, opp.product_id) if opp.product_id else None
        asset = AssetService.get_asset(db, opp.asset_id) if opp.asset_id else None
        
        brand = BrandService.get_vehicle_spec(db, opp.brand_id) if opp.brand_id else None
        model = ModelService.get_model(db, opp.model_id) if opp.model_id else None

        details = {
            "Opportunity Name": opp.name,
            "Stage": opp.stage,
            "Amount": opp.amount if opp.amount else 0,
            "Temperature": opp.temperature,
            "Close Date": opp.close_date,
            "Account": account.name if account else None,
            "Account_Hidden_Ref": opp.account_id,
            "Brand": brand.name if brand else None,
            "Brand_Hidden_Ref": opp.brand_id,
            "Model": model.name if model else None,
            "Model_Hidden_Ref": opp.model_id,
            "Product": product.name if product else None,
            "Product_Hidden_Ref": opp.product_id,
            "Asset": asset.name if asset else None,
            "Asset_Hidden_Ref": opp.asset_id
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
            "request": request,
            "object_type": "Opportunity",
            "plural_type": "opportunities",
            "record_id": opp_id,
            "record_name": opp.name,
            "details": details,
            "path": path,
            "is_followed": opp.is_followed,
            "created_at": opp.created_at,
            "updated_at": opp.updated_at,
            "related_lists": []
        })
    except Exception as e:
        logger.error(f"Opportunity Detail error: {e}")
        return RedirectResponse(url=f"/opportunities?error=Error+loading+opportunity+detail:+{str(e).replace(' ', '+')}")

@router.get("/opportunities")
async def list_opportunities(request: Request, filter: str = None, db: Session = Depends(get_db)):
    try:
        query = db.query(models.Opportunity).filter(models.Opportunity.deleted_at == None)
        
        if filter == "recommend":
             # Recommend Sales: Test Drive or Closed Won
             query = query.filter(models.Opportunity.stage.in_(["Test Drive", "Closed Won"]))
             
        opps = query.all()
        items = []
        for o in opps:
            created_str = ""
            if o.created_at:
                if isinstance(o.created_at, datetime):
                    created_str = o.created_at.strftime("%Y-%m-%d")
                else:
                    created_str = str(o.created_at)[:10]

            model = ModelService.get_model(db, o.model_id) if o.model_id else None
            items.append({
                "id": o.id,
                "name": o.name,
                "amount": o.amount if o.amount else 0,
                "stage": o.stage,
                "model": model.name if model else "",
                "created": created_str,
                "edit_url": f"/opportunities/new-modal?id={o.id}"
            })
        columns = ["name", "amount", "stage", "model", "created"]
        return templates.TemplateResponse("list_view.html", {
            "request": request, 
            "object_type": "Opportunity", 
            "plural_type": "opportunities",
            "items": items, 
            "columns": columns
        })
    except Exception as e:
        logger.error(f"List opportunities error: {e}")
        return RedirectResponse(url="/?error=Error+loading+opportunities")

@router.post("/opportunities/{opp_id}")
async def update_opportunity(
    opp_id: str,
    account_id: str = Form(None),
    asset_id: str = Form(None),
    product_id: str = Form(None),
    name: str = Form(...),
    amount: int = Form(0),
    stage: str = Form("Prospecting"),
    status: str = Form("Open"),
    probability: int = Form(10),
    brand_id: str = Form(None),
    model_id: str = Form(None),
    db: Session = Depends(get_db)
):
    OpportunityService.update_opportunity(
        db, opp_id, account_id=account_id, name=name, amount=amount, 
        stage=stage, status=status, probability=probability,
        brand_id=brand_id, model_id=model_id,
        asset_id=asset_id, product_id=product_id
    )
    return RedirectResponse(url=f"/opportunities/{opp_id}?success=Record+updated+successfully", status_code=303)

@router.post("/opportunities/{opp_id}/delete")
async def delete_opportunity(request: Request, opp_id: str, db: Session = Depends(get_db)):
    OpportunityService.delete_opportunity(db, opp_id)
    if "application/json" in request.headers.get("Accept", ""):
        return {"status": "success", "message": "Record deleted successfully"}
    return RedirectResponse(url="/opportunities?success=Record+deleted+successfully", status_code=303)


@router.post("/opportunities/{opp_id}/stage")
async def update_opportunity_stage_endpoint(opp_id: str, stage: str = Form(...), db: Session = Depends(get_db)):
    OpportunityService.update_stage(db, opp_id, stage)
    return {"status": "success", "new_stage": stage}

@router.post("/opportunities/{opp_id}/restore")
async def restore_opportunity_endpoint(opp_id: str, db: Session = Depends(get_db)):
    OpportunityService.restore_opportunity(db, opp_id)
    return {"status": "success"}

@router.post("/opportunities")
async def create_opportunity(
    account_id: str = Form(None),
    asset_id: str = Form(None),
    product_id: str = Form(None),
    name: str = Form(...),
    amount: int = Form(0),
    stage: str = Form("Prospecting"),
    status: str = Form("Open"),
    probability: int = Form(10),
    brand_id: str = Form(None),
    model_id: str = Form(None),
    db: Session = Depends(get_db)
):
    try:
        opp = OpportunityService.create_opportunity(
            db, account_id=account_id, name=name, amount=amount, 
            stage=stage, status=status, probability=probability,
            brand_id=brand_id, model_id=model_id,
            asset_id=asset_id, product_id=product_id
        )
        return RedirectResponse(url=f"/opportunities/{opp.id}?success=Record+created+successfully", status_code=303)
    except Exception as e:
        logger.error(f"Create Opportunity error: {e}")
        return RedirectResponse(url=f"/opportunities?error=Error+creating+opportunity:+{str(e).replace(' ', '+')}", status_code=303)
