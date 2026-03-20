from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from ..database import get_db
from ..services.opportunity_service import OpportunityService
from ..services.message_template_service import MessageTemplateService
from pydantic import BaseModel
from ..models import Account, Opportunity, Model, MessageTemplate
from ..core.templates import templates

router = APIRouter(prefix="/messaging", tags=["Messaging"])

class TemplateCreate(BaseModel):
    name: str
    body: str
    record_type: str = "SMS" # Default to SMS

@router.get("/ui", response_class=HTMLResponse)
async def messaging_ui(request: Request, db: Session = Depends(get_db)):
    # Fetch only Accounts that have at least one Opportunity
    opp_accounts = db.query(Account).join(Opportunity, Account.id == Opportunity.account_id).distinct().all()
    
    # Fetch opportunities with joined model names for display
    opportunities = db.query(Opportunity).filter(Opportunity.deleted_at == None).all()
    # Ensure model names are accessible (SQLAlchemy relationships should handle this if defined)
    
    message_templates = MessageTemplateService.get_templates(db)
    
    return templates.TemplateResponse("send_message.html", {
        "request": request,
        "accounts": opp_accounts,
        "opportunities": opportunities,
        "templates": message_templates
    })

@router.post("/templates")
async def create_template(data: TemplateCreate, db: Session = Depends(get_db)):
    # Check if a template with this name exists
    existing = db.query(MessageTemplate).filter(MessageTemplate.name == data.name).first()
    if existing:
        return MessageTemplateService.update_template(db, existing.id, body=data.body, record_type=data.record_type)
    return MessageTemplateService.create_template(db, name=data.name, body=data.body, record_type=data.record_type)
