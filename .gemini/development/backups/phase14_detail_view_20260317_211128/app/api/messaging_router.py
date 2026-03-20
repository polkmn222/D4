import os
import shutil
import uuid
from fastapi import APIRouter, Depends, Request, File, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse
from sqlalchemy.orm import Session
from ..database import get_db
from ..services.opportunity_service import OpportunityService
from ..services.message_template_service import MessageTemplateService
from pydantic import BaseModel
from ..models import Contact, Opportunity, Model, MessageTemplate
from ..core.templates import templates

from typing import Optional

router = APIRouter(prefix="/messaging", tags=["Messaging"])

class TemplateCreate(BaseModel):
    id: Optional[str] = None
    name: str
    content: str
    record_type: str = "SMS" # Default to SMS
    file_path: Optional[str] = None

@router.get("/ui", response_class=HTMLResponse)
async def messaging_ui(request: Request, db: Session = Depends(get_db)):
    # Fetch only Contacts that have at least one Opportunity
    opp_contacts = db.query(Contact).join(Opportunity, Contact.id == Opportunity.contact).distinct().all()
    
    # Fetch opportunities with joined Contact and Model for display
    results = db.query(Opportunity, Contact, Model)\
        .join(Contact, Opportunity.contact == Contact.id)\
        .outerjoin(Model, Opportunity.model == Model.id)\
        .filter(Opportunity.deleted_at == None, Contact.deleted_at == None)\
        .filter(Contact.phone != None, Contact.phone != "")\
        .order_by(Opportunity.created_at.desc())\
        .all()

    opportunities_data = []
    for opp, contact, mod in results:
        opportunities_data.append({
            "id": opp.id,
            "name": opp.name,
            "stage": opp.stage,
            "created_at": opp.created_at,
            "contact": {"name": f"{contact.first_name if contact.first_name else ''} {contact.last_name if contact.last_name else ''}".strip() or contact.name or "Unnamed", "phone": contact.phone},
            "model": {"name": mod.name} if mod else None
        })
    
    message_templates = MessageTemplateService.get_templates(db)
    
    return templates.TemplateResponse("messages/send_message.html", {
        "request": request,
        "contacts": opp_contacts,
        "opportunities": opportunities_data,
        "templates": message_templates
    })

@router.get("/recommendations")
async def get_messaging_recommendations(db: Session = Depends(get_db)):
    """
    Returns AI recommended opportunities (now pre-filtered for phone numbers by the service).
    """
    recommended_opps = OpportunityService.get_ai_recommendations(db, limit=20)
    
    results_data = []
    for opp in recommended_opps:
        contact = db.query(Contact).filter(Contact.id == opp.contact).first()
        mod = db.query(Model).filter(Model.id == opp.model).first() if opp.model else None
        
        results_data.append({
            "id": opp.id,
            "name": opp.name,
            "stage": opp.stage,
            "created_at": opp.created_at.strftime('%Y-%m-%d') if opp.created_at else '-',
            "contact": {"name": f"{contact.first_name if contact.first_name else ''} {contact.last_name if contact.last_name else ''}".strip() or contact.name or "Unnamed", "phone": contact.phone},
            "model": {"name": mod.name} if mod else None
        })
        
    return results_data


@router.get("/default_recipients")
async def get_default_recipients(db: Session = Depends(get_db)):
    """
    Returns the default list of opportunities that have a phone number.
    """
    results = db.query(Opportunity, Contact, Model)\
        .join(Contact, Opportunity.contact == Contact.id)\
        .outerjoin(Model, Opportunity.model == Model.id)\
        .filter(Opportunity.deleted_at == None, Contact.deleted_at == None)\
        .filter(Contact.phone != None, Contact.phone != "")\
        .order_by(Opportunity.created_at.desc())\
        .all()

    opportunities_data = []
    for opp, contact, mod in results:
        opportunities_data.append({
            "id": opp.id,
            "name": opp.name,
            "stage": opp.stage,
            "created_at": opp.created_at.strftime('%Y-%m-%d') if opp.created_at else '-',
            "contact": {"name": f"{contact.first_name if contact.first_name else ''} {contact.last_name if contact.last_name else ''}".strip() or contact.name or "Unnamed", "phone": contact.phone},
            "model": {"name": mod.name} if mod else None
        })
    return opportunities_data

@router.post("/templates/upload")
async def upload_template_image(file: UploadFile = File(...)):
    """Uploads an image for a message template (MMS)"""
    # Only allow PNG
    if not file.filename.endswith(".png"):
        return JSONResponse(status_code=400, content={"message": "Only PNG files are allowed."})
    
    # Create directory if not exists
    upload_dir = "app/static/uploads/templates"
    if not os.path.exists(upload_dir):
        os.makedirs(upload_dir)
        
    file_extension = os.path.splitext(file.filename)[1]
    unique_filename = f"{uuid.uuid4()}{file_extension}"
    file_path = os.path.join(upload_dir, unique_filename)
    
    # Resolve relative to project root
    abs_path = os.path.abspath(file_path)
    os.makedirs(os.path.dirname(abs_path), exist_ok=True)

    with open(abs_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    return {"file_path": f"/static/uploads/templates/{unique_filename}"}

@router.post("/templates")
async def create_template(data: TemplateCreate, db: Session = Depends(get_db)):
    if data.id:
        existing = MessageTemplateService.get_template(db, data.id)
        if existing:
            return MessageTemplateService.update_template(db, data.id, 
                name=data.name, 
                content=data.content, 
                record_type=data.record_type,
                file_path=data.file_path
            )
    
    # Fallback to name check if no ID
    existing = db.query(MessageTemplate).filter(MessageTemplate.name == data.name).first()
    if existing:
        return MessageTemplateService.update_template(db, existing.id, 
            content=data.content, 
            record_type=data.record_type,
            file_path=data.file_path
        )
        
    return MessageTemplateService.create_template(db, 
        name=data.name, 
        content=data.content, 
        record_type=data.record_type,
        file_path=data.file_path
    )

@router.delete("/templates/{template_id}")
async def delete_template(template_id: str, db: Session = Depends(get_db)):
    MessageTemplateService.delete_template(db, template_id)
    return {"status": "success"}
