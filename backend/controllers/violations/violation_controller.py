from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.db.database import get_db
from backend.db.repositories.violations.repository import ViolationRepository
from backend.schemas.violations.schema import ViolationResponse
from backend.services.violations.violation_service import ViolationService

router = APIRouter(tags=["violations"])


def get_violation_service(db: Session = Depends(get_db)) -> ViolationService:
    return ViolationService(violation_repository=ViolationRepository(db))


@router.get("/violations", response_model=list[ViolationResponse])
def list_violations(
    client_id: Optional[str] = Query(default=None),
    service: ViolationService = Depends(get_violation_service),
) -> list[ViolationResponse]:
    violations = service.list_violations(client_id=client_id)
    return [ViolationResponse.model_validate(violation) for violation in violations]
