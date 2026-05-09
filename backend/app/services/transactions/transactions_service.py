from fastapi import UploadFile
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from backend.app.repositories.positions import PositionRepository
from backend.app.repositories.transactions import TransactionRepository
from backend.app.repositories.violations import ViolationRepository
from backend.app.api.schemas.transactions import TransactionUploadResponse
from backend.app.services.positions import build_position_snapshots
from backend.app.services.violations import (
    detect_violations,
    validate_transactions_can_build_positions,
)
from backend.app.services.shared.math_utils import calculate_fifo_positions
from backend.app.services.transactions.helpers.ingestion import process_transaction_upload
from backend.app.services.transactions.helpers.responses import (
    failure_response,
    success_response,
)
from backend.app.utils.exceptions import (
    DuplicateTransactionError,
    PersistenceError,
)


async def upload_transactions(
    file: UploadFile,
    db: Session,
) -> TransactionUploadResponse:
    transactions = TransactionRepository(db)
    positions = PositionRepository(db)
    violations = ViolationRepository(db)

    ingestion = await process_transaction_upload(file)
    if ingestion.has_errors:
        return failure_response(ingestion)

    impacted_client_ids = sorted({record.client_id for record in ingestion.records})

    try:
        transactions.add_records(ingestion.records)
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
        )
        violations.update_clients_violations(impacted_client_ids, detected_violations)

        db.commit()
    except IntegrityError as exc:
        db.rollback()
        if transactions.is_duplicate_transaction_id_error(exc):
            raise DuplicateTransactionError() from exc
        raise PersistenceError(
            "Failed to persist uploaded transactions and positions."
        ) from exc
    except SQLAlchemyError as exc:
        db.rollback()
        raise PersistenceError(
            "Failed to persist uploaded transactions and positions."
        ) from exc
    except Exception:
        db.rollback()
        raise

    return success_response(ingestion)
