from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.db.session import get_db
from backend.schemas.common import TODO_RESPONSES
from backend.services.analytics_service import AnalyticsService
from backend.utils.responses import todo_response

router = APIRouter(tags=["analytics"])


class AnalyticsController:
    def __init__(self, db: Session) -> None:
        self.service = AnalyticsService(db=db)

    def get_analytics(self):
        # TODO: add analytics response mapping.
        try:
            return self.service.get_analytics()
        except NotImplementedError as exc:
            return todo_response(str(exc), endpoint="GET /analytics")


def get_analytics_controller(db: Session = Depends(get_db)) -> AnalyticsController:
    return AnalyticsController(db=db)


@router.get("/analytics", responses=TODO_RESPONSES)
def get_analytics(controller: AnalyticsController = Depends(get_analytics_controller)):
    # TODO: expose portfolio and compliance analytics.
    return controller.get_analytics()
