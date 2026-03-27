from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
import os

# Create the sub-app
app = FastAPI(title="Agent Gem Sub-app", version="1.0.0")

# Determine base directory for Agent Gem
# current file: development/agent(gem)/backend/main.py
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATIC_DIR = os.path.join(BASE_DIR, "frontend", "static")

# Mount static files within the sub-app
# If sub-app is mounted at /agent-gem in main app, 
# then /agent-gem/static will serve these files.
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="agent_gem_static")

# Import and include the local router
from agent_gem.backend.router import router as agent_router
app.include_router(agent_router)

@app.get("/health")
async def health_check():
    return {"status": "ok", "module": "agent_gem"}
