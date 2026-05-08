from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.controller.analytics_controller import AnalyticsController
from backend.db.session import get_db
from backend.schemas.common import TODO_RESPONSES

router = APIRouter(tags=["analytics"])


def get_analytics_controller(db: Session = Depends(get_db)) -> AnalyticsController:
    return AnalyticsController(db=db)


@router.get("/analytics", responses=TODO_RESPONSES)
def get_analytics(controller: AnalyticsController = Depends(get_analytics_controller)):
    # TODO: expose portfolio and compliance analytics.
    return controller.get_analytics()
