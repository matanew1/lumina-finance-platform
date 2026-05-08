from fastapi import APIRouter

from backend.routes.analytics_routes import router as analytics_router
from backend.routes.client_routes import router as client_router
from backend.routes.position_routes import router as position_router
from backend.routes.transaction_routes import router as transaction_router
from backend.routes.violation_routes import router as violation_router

router = APIRouter()

router.include_router(transaction_router)
router.include_router(client_router)
router.include_router(position_router)
router.include_router(violation_router)
router.include_router(analytics_router)
