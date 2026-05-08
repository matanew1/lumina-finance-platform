from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.db.session import get_db
from backend.schemas.common import TODO_RESPONSES
from backend.services.violation_service import ViolationService
from backend.utils.responses import todo_response

router = APIRouter(tags=["violations"])


class ViolationController:
    def __init__(self, db: Session) -> None:
        self.service = ViolationService(db=db)

    def get_violations(self):
        # TODO: add request parameters and response mapping.
        try:
            return self.service.get_violations()
        except NotImplementedError as exc:
            return todo_response(str(exc), endpoint="GET /violations")


def get_violation_controller(db: Session = Depends(get_db)) -> ViolationController:
    return ViolationController(db=db)


@router.get("/violations", responses=TODO_RESPONSES)
def get_violations(controller: ViolationController = Depends(get_violation_controller)):
    # TODO: support violation filters and paging.
    return controller.get_violations()
