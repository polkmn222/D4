from fastapi import APIRouter, Request, Depends
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from ...database import get_db
from ...services.dashboard_service import DashboardService
from ...services.search_service import SearchService
from ...services.opportunity_service import OpportunityService
from ...core.templates import templates
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/")
async def dashboard(request: Request, db: Session = Depends(get_db)):
    try:
        logger.debug("Entering dashboard endpoint")
        data = DashboardService.get_dashboard_data(db)
        
        return templates.TemplateResponse("dashboard.html", {
            "request": request, 
            **data
        })
    except Exception as e:
        logger.error(f"Dashboard error: {e}")
        return RedirectResponse(url="/leads?error=Error+loading+dashboard")

@router.get("/api/recommendations")
async def get_ai_recommendations(db: Session = Depends(get_db)):
    recommended_opps = OpportunityService.get_ai_recommendations(db, limit=5)
    return templates.TemplateResponse("dashboard_ai_recommend_fragment.html", {
        "request": {},
        "recommended_opportunities": recommended_opps
    })

@router.get("/search")
async def global_search(request: Request, q: str = "", db: Session = Depends(get_db)):
    logger.debug(f"Entering global_search endpoint with query: {q}")
    results = SearchService.global_search(db, q)
    return templates.TemplateResponse("search_results.html", {"request": request, "query": q, "results": results})
