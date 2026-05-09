from fastapi import UploadFile
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from backend.app.repositories.positions import PositionRepository
from backend.app.repositories.transactions import TransactionRepository
from backend.app.repositories.violations import ViolationRepository
from backend.app.schemas.transactions import TransactionUploadResponse
from backend.app.services.positions import build_position_snapshots
from backend.app.services.positions.helpers.fifo_engine import calculate_fifo_positions
from backend.app.services.transactions.helpers.ingestion import process_transaction_upload
from backend.app.services.transactions.helpers.responses import (
    failure_response,
    success_response,
)
from backend.app.services.violations import (
    PERSISTED_RULES,
    detect_violations,
    validate_transactions_can_build_positions,
)
from backend.app.utils.exceptions import (
    DuplicateTransactionError,
    PersistenceError,
)


async def upload_transactions_by_file(
    file: UploadFile,
    db: Session,
) -> TransactionUploadResponse:
    """Validate and persist a transaction file, then recompute positions and violations."""
    transactions = TransactionRepository(db)
    positions = PositionRepository(db)
    violations = ViolationRepository(db)

    process_results = await process_transaction_upload(file)
    if process_results.has_errors:
        return failure_response(process_results)

    impacted_client_ids = sorted({record.client_id for record in process_results.records})

    incoming_ids = [record.transaction_id for record in process_results.records]
    has_within_batch_duplicates = len(set(incoming_ids)) != len(incoming_ids)
    if has_within_batch_duplicates or transactions.find_existing_transaction_ids(incoming_ids):
        raise DuplicateTransactionError()

    try:
        transactions.add_records(process_results.records)
        ordered_transactions = transactions.list_for_clients_ordered(impacted_client_ids)

        validate_transactions_can_build_positions(ordered_transactions)

        calculated_positions = calculate_fifo_positions(ordered_transactions)
        positions.update_clients_positions(impacted_client_ids, calculated_positions)

        position_snapshots = build_position_snapshots(
            ordered_transactions,
            calculated_positions,
        )
        detected_violations = detect_violations(
            ordered_transactions,
            position_snapshots,
            PERSISTED_RULES,
        )
        violations.update_clients_violations(impacted_client_ids, detected_violations)

        db.commit()
    except SQLAlchemyError as exc:
        db.rollback()
        raise PersistenceError(
            "Failed to persist uploaded transactions and positions."
        ) from exc
    except Exception:
        db.rollback()
        raise

    return success_response(process_results)
