from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from ...database import get_db
from ...services.campaign_service import CampaignService
from ...models import Campaign
from ... import models
from ...core.templates import templates
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/campaigns/{campaign_id}")
async def campaign_detail(request: Request, campaign_id: str, db: Session = Depends(get_db)):
    try:
        logger.info(f"Accessing Campaign Detail: {campaign_id}")
        campaign = CampaignService.get_campaign(db, campaign_id)
        if not campaign: return RedirectResponse(url="/campaigns?error=Campaign+not+found")
        details = {
            "Name": campaign.name,
            "Status": campaign.status,
            "Type": campaign.type,
            "Description": campaign.description,
            "Start Date": campaign.start_date.strftime("%Y-%m-%d") if campaign.start_date else "N/A",
            "End Date": campaign.end_date.strftime("%Y-%m-%d") if campaign.end_date else "N/A"
        }
        return templates.TemplateResponse("detail_view.html", {
            "request": request, "object_type": "Campaign", "plural_type": "campaigns",
            "record_id": campaign_id, "record_name": campaign.name, "details": details,
            "created_at": campaign.created_at, "updated_at": campaign.updated_at,
            "related_lists": []
        })
    except Exception as e:
        logger.error(f"Error loading campaign detail: {e}")
        return RedirectResponse(url=f"/campaigns?error=Error+loading+campaign+detail:+{str(e).replace(' ', '+')}")

@router.get("/campaigns")
async def list_campaigns(request: Request, db: Session = Depends(get_db)):
    campaigns = CampaignService.get_campaigns(db)
    items = []
    for c in campaigns:
        items.append({
            "id": c.id,
            "name": c.name,
            "status": c.status,
            "type": c.type or "Social Media",
            "edit_url": f"/campaigns/new?id={c.id}"
        })
    columns = ["name", "type", "status"]
    return templates.TemplateResponse("list_view.html", {
        "request": request, 
        "object_type": "Campaign", 
        "plural_type": "campaigns",
        "items": items, 
        "columns": columns
    })

@router.post("/campaigns")
async def create_campaign(
    name: str = Form(...),
    type: str = Form("Social Media"),
    status: str = Form("Planned"),
    description: str = Form(None),
    db: Session = Depends(get_db)
):
    campaign = CampaignService.create_campaign(db, name=name, type=type, status=status, description=description)
    return RedirectResponse(url=f"/campaigns/{campaign.id}?success=Record+created+successfully", status_code=303)

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
    return RedirectResponse(url=f"/campaigns/{campaign_id}" + "?success=Record+updated+successfully", status_code=303)

@router.post("/campaigns/{campaign_id}/delete")
async def delete_campaign(request: Request, campaign_id: str, db: Session = Depends(get_db)):
    CampaignService.delete_campaign(db, campaign_id)
    if "application/json" in request.headers.get("Accept", ""):
        return {"status": "success", "message": "Record deleted successfully"}
    return RedirectResponse(url="/campaigns?success=Record+deleted+successfully", status_code=303)

@router.post("/campaigns/{campaign_id}/restore")
async def restore_campaign_endpoint(campaign_id: str, db: Session = Depends(get_db)):
    cmp = db.query(models.Campaign).filter(models.Campaign.id == campaign_id).first()
    if cmp:
        cmp.deleted_at = None
        db.commit()
    return {"status": "success"}
