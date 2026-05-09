from fastapi import UploadFile
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from backend.db.repositories.transactions.repository import TransactionRepository
from backend.services.positions.position_service import PositionService
from backend.services.transactions.transaction_ingestion import TransactionIngestionService
from backend.services.transactions.types import (
    TransactionIngestionResult,
    TransactionRecord,
    TransactionUploadResponse,
)
from backend.services.violations.violation_service import ViolationService
from backend.utils.errors.exceptions import BadRequestError, ConflictError, PersistenceError


class TransactionService:
    def __init__(
        self,
        transaction_repository: TransactionRepository,
        position_service: PositionService,
        violation_service: ViolationService,
        db: Session,
        ingestion_service: TransactionIngestionService | None = None,
    ) -> None:
        self.transaction_repository = transaction_repository
        self.position_service = position_service
        self.violation_service = violation_service
        self.db = db
        self.ingestion_service = ingestion_service or TransactionIngestionService()

    async def upload_transactions(self, file: UploadFile):
        try:
            ingestion = await self.ingestion_service.read_normalized_records(file)
        except ValueError as exc:
            raise BadRequestError(str(exc)) from exc

        if ingestion.has_errors:
            return self._failure_response(ingestion)

        records = ingestion.records
        impacted_client_ids = self._client_ids_from_records(records)

        try:
            transactions = self._persist_upload(records, impacted_client_ids)

            self.violation_service.validate_transactions_can_build_positions(transactions)

            positions = self.position_service.update_clients_positions(
                impacted_client_ids,
                transactions,
            )

            self.violation_service.refresh_clients_violations(
                impacted_client_ids,
                transactions,
                positions,
            )

            self.db.commit()
        except ValueError as exc:
            self.db.rollback()
            raise BadRequestError(str(exc)) from exc
        except BadRequestError:
            self.db.rollback()
            raise
        except IntegrityError as exc:
            self.db.rollback()
            if self.transaction_repository.is_duplicate_transaction_id_error(exc):
                raise ConflictError("One or more transactions have duplicate transaction IDs.") from exc
            raise PersistenceError("Failed to persist uploaded transactions and positions.") from exc
        except SQLAlchemyError as exc:
            self.db.rollback()
            raise PersistenceError("Failed to persist uploaded transactions and positions.") from exc

        return self._success_response(ingestion)

    def _persist_upload(self, records: list[TransactionRecord], client_ids: list[str]) -> list:
        self.transaction_repository.add_records(records)
        return self.transaction_repository.list_for_clients_ordered(client_ids)

    @staticmethod
    def _client_ids_from_records(records: list[TransactionRecord]) -> list[str]:
        return sorted({record["client_id"] for record in records})

    @staticmethod
    def _failure_response(result: TransactionIngestionResult) -> TransactionUploadResponse:
        return {
            "status": "failed",
            "total_rows": result.total_rows,
            "valid_rows": result.valid_rows,
            "invalid_rows": result.invalid_rows,
            "persisted_rows": 0,
            "errors": result.errors,
        }

    @staticmethod
    def _success_response(result: TransactionIngestionResult) -> TransactionUploadResponse:
        return {
            "status": "success",
            "total_rows": result.total_rows,
            "valid_rows": result.valid_rows,
            "invalid_rows": 0,
            "persisted_rows": len(result.records),
            "errors": [],
        }
