from fastapi import APIRouter

from backend.controllers.analytics_controller import router as analytics_router
from backend.controllers.client_controller import router as client_router
from backend.controllers.position_controller import router as position_router
from backend.controllers.transaction_controller import router as transaction_router
from backend.controllers.violation_controller import router as violation_router

router = APIRouter()

router.include_router(transaction_router)
router.include_router(client_router)
router.include_router(position_router)
router.include_router(violation_router)
router.include_router(analytics_router)
