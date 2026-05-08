from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.db.session import get_db
from backend.schemas.violation_schema import ViolationRead
from backend.services.violations.violation_service import ViolationService

router = APIRouter(tags=["violations"])


class ViolationController:
    def __init__(self, db: Session) -> None:
        self.service = ViolationService(db=db)

    def list_violations(self, client_id: Optional[str] = None) -> list[ViolationRead]:
        violations = self.service.list_violations(client_id=client_id)
        return [ViolationRead.model_validate(violation) for violation in violations]


def get_violation_controller(db: Session = Depends(get_db)) -> ViolationController:
    return ViolationController(db=db)


@router.get("/violations", response_model=list[ViolationRead])
def list_violations(
    client_id: Optional[str] = Query(default=None),
    controller: ViolationController = Depends(get_violation_controller),
) -> list[ViolationRead]:
    return controller.list_violations(client_id=client_id)
