from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.controller.violation_controller import ViolationController
from backend.db.session import get_db
from backend.schemas.common import TODO_RESPONSES

router = APIRouter(tags=["violations"])


def get_violation_controller(db: Session = Depends(get_db)) -> ViolationController:
    return ViolationController(db=db)


@router.get("/violations", responses=TODO_RESPONSES)
def get_violations(controller: ViolationController = Depends(get_violation_controller)):
    # TODO: support violation filters and paging.
    return controller.get_violations()
