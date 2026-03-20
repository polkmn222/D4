from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from .services.contact_service import init_db
from .api.web_router import router as web_router

app = FastAPI(title="AI Ready CRM")

# Mount Static Files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

@app.on_event("startup")
def on_startup():
    init_db()

# Include Web Router
app.include_router(web_router)
