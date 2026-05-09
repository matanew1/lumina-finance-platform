from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.app.db.session import get_db
from backend.app.repositories.violations import ViolationRepository
from backend.app.schemas.violations import ViolationResponse
from backend.app.services.violations import list_violations as list_violations_use_case

router = APIRouter(tags=["violations"])


@router.get(
    "/violations",
    response_model=list[ViolationResponse],
)
def list_violations(
    client_id: str | None = Query(default=None),
    db: Session = Depends(get_db),
) -> list[ViolationResponse]:
    return list_violations_use_case(
        repository=ViolationRepository(db),
        client_id=client_id,
    )
