from sqlalchemy.orm import Session

from backend.services.analytics_service import AnalyticsService
from backend.utils.responses import todo_response


class AnalyticsController:
    def __init__(self, db: Session) -> None:
        self.service = AnalyticsService(db=db)

    def get_analytics(self):
        # TODO: add analytics response mapping.
        try:
            return self.service.get_analytics()
        except NotImplementedError as exc:
            return todo_response(str(exc), endpoint="GET /analytics")
