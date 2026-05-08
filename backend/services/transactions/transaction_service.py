from fastapi import UploadFile
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from backend.db.repositories.position_repository import PositionRepository
from backend.db.repositories.transaction_repository import TransactionRepository
from backend.services.positions.fifo_calculator import calculate_fifo_positions
from backend.services.transactions.transaction_ingestion import (
    normalize_transaction_dataframe,
    read_transaction_file,
    transaction_records_from_dataframe,
    validate_transaction_dataframe,
)
from backend.utils.exceptions import BadRequestError, ConflictError, PersistenceError


class TransactionService:
    def __init__(
        self,
        db: Session,
        transaction_repository: TransactionRepository | None = None,
        position_repository: PositionRepository | None = None,
    ) -> None:
        self.db = db
        self.transaction_repository = transaction_repository or TransactionRepository(db)
        self.position_repository = position_repository or PositionRepository(db)

    async def upload_transactions(self, file: UploadFile):
        try:
            dataframe = await read_transaction_file(file)
            normalized = normalize_transaction_dataframe(dataframe)
        except ValueError as exc:
            raise BadRequestError(str(exc)) from exc

        errors = validate_transaction_dataframe(normalized)

        total_rows = len(normalized)
        invalid_row_numbers = {error["row_number"] for error in errors if error["row_number"] is not None}
        valid_rows = total_rows - len(invalid_row_numbers)

        if errors:
            return {
                "status": "failed",
                "total_rows": total_rows,
                "valid_rows": valid_rows,
                "invalid_rows": len(invalid_row_numbers),
                "persisted_rows": 0,
                "errors": errors,
            }

        # Convert valid rows to Transaction records and persist to the database
        records = transaction_records_from_dataframe(normalized)
        impacted_client_ids = sorted({record["client_id"] for record in records})

        try:
            # Persist transactions
            self.transaction_repository.add_records(records)
            transactions = self.transaction_repository.list_for_clients_ordered(impacted_client_ids)
            
            # Calculate new positions based on the impacted transactions and persist updated positions
            positions = calculate_fifo_positions(transactions)
            self.position_repository.update_client_positions(impacted_client_ids, positions)
            
            # Commit
            self.db.commit()
        except ValueError as exc:
            self.db.rollback()
            raise BadRequestError(str(exc)) from exc
        except IntegrityError as exc:
            self.db.rollback()
            if self.transaction_repository.is_duplicate_transaction_id_error(exc):
                raise ConflictError("One or more transactions have duplicate transaction IDs.") from exc
            raise PersistenceError("Failed to persist uploaded transactions and positions.") from exc
        except SQLAlchemyError as exc:
            self.db.rollback()
            raise PersistenceError("Failed to persist uploaded transactions and positions.") from exc

        return {
            "status": "success",
            "total_rows": total_rows,
            "valid_rows": total_rows,
            "invalid_rows": 0,
            "persisted_rows": len(records),
            "errors": [],
        }
