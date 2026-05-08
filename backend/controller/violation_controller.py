from sqlalchemy.orm import Session

from backend.services.violation_service import ViolationService
from backend.utils.responses import todo_response


class ViolationController:
    def __init__(self, db: Session) -> None:
        self.service = ViolationService(db=db)

    def get_violations(self):
        # TODO: add request parameters and response mapping.
        try:
            return self.service.get_violations()
        except NotImplementedError as exc:
            return todo_response(str(exc), endpoint="GET /violations")
