from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from agent.ui.backend.router import router


app = FastAPI(title="D5 Command Agent")

CURRENT_FILE = Path(__file__).resolve()
AGENT_ROOT = CURRENT_FILE.parents[2]
STATIC_DIR = AGENT_ROOT / "ui" / "frontend" / "static"

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="agent_static")
app.include_router(router)

