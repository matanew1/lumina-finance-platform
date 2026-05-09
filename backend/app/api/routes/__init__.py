from fastapi import APIRouter

from backend.app.api.routes.analytics import router as analytics_router
from backend.app.api.routes.clients import router as clients_router
from backend.app.api.routes.positions import router as positions_router
from backend.app.api.routes.transactions import router as transactions_router
from backend.app.api.routes.violations import router as violations_router

router = APIRouter()
router.include_router(transactions_router)
router.include_router(clients_router)
router.include_router(positions_router)
router.include_router(violations_router)
router.include_router(analytics_router)
