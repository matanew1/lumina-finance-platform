from sqlalchemy.orm import Session


class AnalyticsService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_analytics(self):
        # TODO: aggregate portfolio, transaction, and violation analytics.
        raise NotImplementedError("TODO: implement analytics service.")
