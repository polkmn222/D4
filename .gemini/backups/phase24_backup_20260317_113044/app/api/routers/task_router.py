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
        acc = AccountService.get_account(db, t.account) if t.account else None
        items.append({
            "id": t.id,
            "name": t.subject if t.subject else "",
            "status": t.status if t.status else "",
            "priority": t.priority if t.priority else "",
            "account": acc.name if acc else "",
            "edit_url": f"/tasks/new-modal?id={t.id}"
        })
    columns = ["name", "status", "priority", "account"]
    return templates.TemplateResponse("tasks/list_view.html", {
        "request": request, "object_type": "Task", "plural_type": "tasks",
        "items": items, "columns": columns
    })

@router.get("/tasks/{task_id}")
async def task_detail(request: Request, task_id: str, db: Session = Depends(get_db)):
    task = TaskService.get_task(db, task_id)
    if not task: return RedirectResponse(url="/tasks?error=Task+not+found")
    acc = AccountService.get_account(db, task.account) if task.account else None
    details = {
        "Subject": task.subject if task.subject else "",
        "Status": task.status if task.status else "",
        "Priority": task.priority if task.priority else "",
        "Account": acc.name if acc else "",
        "Account_Hidden_Ref": task.account if task.account else "",
        "Description": task.description if task.description else ""
    }
    return templates.TemplateResponse("tasks/detail_view.html", {
        "request": request, "object_type": "Task", "plural_type": "tasks",
        "record_id": task_id, "record_name": task.subject if task.subject else "Task Detail", "details": details,
        "created_at": task.created_at, "updated_at": task.updated_at, "related_lists": []
    })

@router.post("/tasks")
async def create_task_endpoint(
    subject: str = Form(...),
    status: str = Form("Not Started"),
    priority: str = Form("Normal"),
    account: str = Form(None),
    opportunity: str = Form(None),
    message: str = Form(None),
    description: str = Form(None),
    db: Session = Depends(get_db)
):
    try:
        task = TaskService.create_task(
            db, subject=subject, status=status, priority=priority, 
            account=account, opportunity=opportunity, 
            message=message, description=description
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
    account: str = Form(None),
    opportunity: str = Form(None),
    message: str = Form(None),
    description: str = Form(None),
    db: Session = Depends(get_db)
):
    try:
        TaskService.update_task(
            db, task_id, subject=subject, status=status, priority=priority, 
            account=account, opportunity=opportunity, 
            message=message, description=description
        )
        return RedirectResponse(url=f"/tasks/{task_id}?success=Record+updated+successfully", status_code=303)
    except Exception as e:
        logger.error(f"Error updating task: {e}")
        return RedirectResponse(url=f"/tasks/{task_id}?error=Error+updating+record")

@router.post("/tasks/{task_id}/delete")
async def delete_task_route(request: Request, task_id: str, db: Session = Depends(get_db)):
    TaskService.delete(db, task_id)
    if request.headers.get("Accept") == "application/json":
        return {"status": "success", "message": "Record deleted"}
    return RedirectResponse(url="/tasks?success=Deleted", status_code=303)
