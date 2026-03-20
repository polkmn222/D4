from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from ...database import get_db
from ...services.account_service import AccountService
from ...services.contact_service import ContactService
from ...services.opportunity_service import OpportunityService
from ...services.asset_service import AssetService
from ...core.templates import templates
import logging

from ...core.enums import RecordType, AccountStatus

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/accounts/{account_id}")
async def account_detail(request: Request, account_id: str, db: Session = Depends(get_db)):
    try:
        account = AccountService.get_account(db, account_id)
        if not account:
            return RedirectResponse(url="/accounts?error=Account+not+found")
        
        details = {
            "Name": account.name,
            "Record Type": account.record_type,
            "Phone": account.phone,
            "Email": account.email,
            "Industry": account.industry,
            "Website": account.website,
            "Status": account.status,
            "Created Date": account.created_at.strftime("%Y-%m-%d %H:%M") if account.created_at else None
        }
        
        # Related tab data
        contacts = ContactService.get_contacts(db, account=account_id)
        opps = OpportunityService.get_by_account(db, account=account_id)
        assets = AssetService.get_assets(db, account=account_id)
        
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
                "items": [{"name": o.name, "stage": o.stage, "amount": o.amount if o.amount else 0, "close_date": o.close_date} for o in opps]
            })
        if assets:
            related_lists.append({
                "title": "Assets",
                "columns": ["name", "vin", "status"],
                "items": [{"name": a.name, "vin": a.vin, "status": a.status} for a in assets]
            })

        return templates.TemplateResponse("accounts/detail_view.html", {
            "request": request, "object_type": "Account", "plural_type": "accounts",
            "record_id": account_id, "record_name": account.name,
            "details": details, "created_at": account.created_at,
            "updated_at": account.updated_at, "related_lists": related_lists
        })
        
    except Exception as e:
        logger.error(f"Error loading account detail: {e}")
        return RedirectResponse(url=f"/accounts?error=Error+loading+account+detail:+{str(e).replace(' ', '+')}")

@router.get("/accounts")
async def list_accounts(request: Request, db: Session = Depends(get_db)):
    try:
        accounts = AccountService.get_accounts(db)
        items = []
        for a in accounts:
            items.append({
                "id": a.id,
                "name": a.name,
                "phone": a.phone if a.phone else "",
                "status": a.status if a.status else "",
                "created": a.created_at.strftime("%Y-%m-%d") if a.created_at else "",
                "edit_url": f"/accounts/new-modal?id={a.id}"
            })
        columns = ["name", "phone", "status", "created"]
        return templates.TemplateResponse("accounts/list_view.html", {
            "request": request, 
            "object_type": "Account", 
            "plural_type": "accounts",
            "items": items, 
            "columns": columns
        })
    except Exception as e:
        logger.error(f"List accounts error: {e}")
        return RedirectResponse(url="/?error=Error+loading+accounts")

@router.post("/accounts")
async def create_account(
    name: str = Form(...),
    record_type: str = Form(RecordType.INDIVIDUAL),
    status: str = Form(AccountStatus.ACTIVE),
    industry: str = Form(None),
    phone: str = Form(None),
    email: str = Form(None),
    website: str = Form(None),
    description: str = Form(None),
    db: Session = Depends(get_db)
):
    try:
        account = AccountService.create_account(
            db, name=name, record_type=record_type, status=status,
            industry=industry, phone=phone, email=email, website=website,
            description=description, 
            is_person_account=(record_type==RecordType.INDIVIDUAL)
        )
        return RedirectResponse(url=f"/accounts/{account.id}?success=Record+created+successfully", status_code=303)
    except Exception as e:
        logger.error(f"Create Account error: {e}")
        return RedirectResponse(url=f"/accounts?error=Error+creating+account:+{str(e).replace(' ', '+')}", status_code=303)

@router.post("/accounts/{account_id}")
async def update_account(
    account_id: str,
    name: str = Form(...),
    industry: str = Form(None),
    phone: str = Form(None),
    email: str = Form(None),
    website: str = Form(None),
    status: str = Form(None),
    description: str = Form(None),
    db: Session = Depends(get_db)
):
    AccountService.update_account(
        db, account_id, name=name, industry=industry, 
        phone=phone, email=email,
        website=website, status=status, description=description
    )
    return RedirectResponse(url=f"/accounts/{account_id}" + "?success=Record+updated+successfully", status_code=303)

@router.post("/accounts/{account_id}/delete")
async def delete_account(request: Request, account_id: str, db: Session = Depends(get_db)):
    AccountService.delete_account(db, account_id)
    if "application/json" in request.headers.get("Accept", ""):
        return {"status": "success", "message": "Record deleted successfully"}
    return RedirectResponse(url="/accounts?success=Record+deleted+successfully", status_code=303)

@router.post("/accounts/{account_id}/restore")
async def restore_account_endpoint(account_id: str, db: Session = Depends(get_db)):
    AccountService.restore_account(db, account_id)
    return {"status": "success"}
