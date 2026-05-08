from collections.abc import Iterable
from typing import Optional

from sqlalchemy import delete, select

from backend.db.models.violation import Violation
from backend.db.repositories.base_repository import BaseRepository
from backend.services.violations.types import ViolationDraft


class ViolationRepository(BaseRepository):
    def list_violations(self, client_id: Optional[str] = None) -> list[Violation]:
        statement = select(Violation)
        if client_id is not None:
            statement = statement.where(Violation.client_id == client_id)
        statement = statement.order_by(Violation.created_at.desc(), Violation.id.desc())
        return list(self.db.scalars(statement).all())

    def update_clients_violations(
        self,
        client_ids: Iterable[str],
        drafts: Iterable[ViolationDraft],
    ) -> None:
        client_id_list = list(client_ids)
        if not client_id_list:
            return

        # Delete existing violations for the impacted clients
        self.db.execute(delete(Violation).where(Violation.client_id.in_(client_id_list)))

        rows = [
            Violation(
                client_id=draft.client_id,
                transaction_id=draft.transaction_id,
                violation_type=draft.violation_type,
                severity=draft.severity,
                message=draft.message,
            )
            for draft in drafts
        ]
        # Insert new violations
        if rows:
            self.db.add_all(rows)

        # Commit the transaction to persist changes to the database  
        self.db.flush()
