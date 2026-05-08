from typing import Optional

from sqlalchemy.orm import Session

from backend.db.repositories.violation_repository import ViolationRepository


class ViolationService:
    def __init__(
        self,
        db: Session,
        violation_repository: Optional[ViolationRepository] = None,
    ) -> None:
        self.violation_repository = violation_repository or ViolationRepository(db)

    def list_violations(self, client_id: Optional[str] = None) -> list:
        return self.violation_repository.list_violations(client_id=client_id)
