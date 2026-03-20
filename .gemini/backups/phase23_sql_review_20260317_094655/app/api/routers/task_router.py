from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from ...database import get_db
from ...services.task_service import TaskService
from ...services.account_service import AccountService
from ...core.templates import templates
from datetime import datetime
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/tasks")
async def list_tasks(request: Request, db: Session = Depends(get_db)):
    tasks = TaskService.get_tasks(db)
    items = []
    for t in tasks:
        acc = AccountService.get_account(db, t.account_id) if t.account_id else None
        items.append({
            "id": t.id,
            "name": t.subject,
            "status": t.status,
            "priority": t.priority,
            "account": acc.name if acc else ""
        })
    columns = ["name", "status", "priority", "account"]
    return templates.TemplateResponse("list_view.html", {
        "request": request, "object_type": "Task", "plural_type": "tasks",
        "items": items, "columns": columns
    })

@router.get("/tasks/{task_id}")
async def task_detail(request: Request, task_id: str, db: Session = Depends(get_db)):
    task = TaskService.get_task(db, task_id)
    if not task: return RedirectResponse(url="/tasks?error=Task+not+found")
    acc = AccountService.get_account(db, task.account_id) if task.account_id else None
    details = {
        "Subject": task.subject,
        "Status": task.status,
        "Priority": task.priority,
        "Account": acc.name if acc else "N/A",
        "Account_Hidden_Ref": task.account_id,
        "Description": task.description
    }
    return templates.TemplateResponse("detail_view.html", {
        "request": request, "object_type": "Task", "plural_type": "tasks",
        "record_id": task_id, "record_name": task.subject, "details": details,
        "created_at": task.created_at, "updated_at": task.updated_at, "related_lists": []
    })

@router.post("/tasks")
async def create_task_endpoint(
    subject: str = Form(...),
    status: str = Form("Not Started"),
    priority: str = Form("Normal"),
    account_id: str = Form(None),
    opportunity_id: str = Form(None),
    message_id: str = Form(None),
    description: str = Form(None),
    db: Session = Depends(get_db)
):
    try:
        task = TaskService.create_task(
            db, subject=subject, status=status, priority=priority, 
            account_id=account_id, opportunity_id=opportunity_id, 
            message_id=message_id, description=description
        )
        return RedirectResponse(url=f"/tasks/{task.id}?success=Record+created+successfully", status_code=303)
    except Exception as e:
        logger.error(f"Error creating task: {e}")
        return RedirectResponse(url="/tasks?error=Error+creating+record")

@router.post("/tasks/{task_id}")
async def update_task_endpoint(
    task_id: str,
    subject: str = Form(...),
    status: str = Form("Not Started"),
    priority: str = Form("Normal"),
    account_id: str = Form(None),
    opportunity_id: str = Form(None),
    message_id: str = Form(None),
    description: str = Form(None),
    db: Session = Depends(get_db)
):
    try:
        TaskService.update_task(
            db, task_id, subject=subject, status=status, priority=priority, 
            account_id=account_id, opportunity_id=opportunity_id, 
            message_id=message_id, description=description
        )
        return RedirectResponse(url=f"/tasks/{task_id}?success=Record+updated+successfully", status_code=303)
    except Exception as e:
        logger.error(f"Error updating task: {e}")
        return RedirectResponse(url=f"/tasks/{task_id}?error=Error+updating+record")

@router.post("/tasks/{task_id}/delete")
async def delete_task_route(request: Request, task_id: str, db: Session = Depends(get_db)):
    TaskService.update_task(db, task_id, deleted_at=datetime.utcnow())
    if "application/json" in request.headers.get("Accept", ""):
        return {"status": "success", "message": "Record deleted successfully"}
    return RedirectResponse(url="/tasks?success=Record+deleted+successfully", status_code=303)
