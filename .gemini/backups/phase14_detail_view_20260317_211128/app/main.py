from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from .api.api_router import api_router
from .database import engine, Base
from . import models
import logging

from .core.toggles import FEATURE_TOGGLES

app = FastAPI(title="AI Ready CRM")

logger = logging.getLogger(__name__)

# Add context processor for Jinja2 templates
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    # This is not a context processor but we can use app.state or similar
    # FastAPI doesn't have a direct context processor like Flask
    # But we can pass it in TemplateResponse
    return await call_next(request)

# Better way: dependency injection or just use it in TemplateResponse
# But to make it available in base.html easily, we can add it to the templates env
from .core.templates import templates
templates.env.globals["FEATURE_TOGGLES"] = FEATURE_TOGGLES

# Mount Static Files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global unhandled exception: {exc}")
    return RedirectResponse(url="/?error=An+unexpected+error+occurred.+Please+try+again.", status_code=303)

@app.exception_handler(404)
async def custom_404_handler(request: Request, __):
    return RedirectResponse(url="/?error=Page+not+found", status_code=303)

# Include API Routers
app.include_router(api_router)

# END FILE
