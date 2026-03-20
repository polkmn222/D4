from fastapi import APIRouter
from .routers import dashboard_router
from . import form_router
from .routers import lead_router
from .routers import contact_router
from .routers import account_router
from .routers import opportunity_router
from .routers import asset_router
from .routers import product_router
from .routers import campaign_router
from .routers import vehicle_spec_router
from .routers import task_router
from .routers import message_router
from .routers import utility_router
from . import messaging_router

api_router = APIRouter()

api_router.include_router(dashboard_router.router)
api_router.include_router(form_router.router)
api_router.include_router(lead_router.router)
api_router.include_router(contact_router.router)
api_router.include_router(account_router.router)
api_router.include_router(opportunity_router.router)
api_router.include_router(asset_router.router)
api_router.include_router(product_router.router)
api_router.include_router(campaign_router.router)
api_router.include_router(vehicle_spec_router.router)
api_router.include_router(task_router.router)
api_router.include_router(message_router.router)
api_router.include_router(utility_router.router)
api_router.include_router(messaging_router.router)
