from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from .api.api_router import api_router
from .database import engine, Base
from . import models

app = FastAPI(title="AI Ready CRM")

# Mount Static Files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)

# Include API Routers
app.include_router(api_router)

# END FILE
