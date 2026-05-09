from fastapi import UploadFile
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from backend.app.repositories.positions import PositionRepository
from backend.app.repositories.transactions import TransactionRepository
from backend.app.repositories.violations import ViolationRepository
from backend.app.schemas.transactions import TransactionUploadResponse
from backend.app.services.positions import build_position_snapshots
from backend.app.services.violations import (
    PERSISTED_RULES,
    detect_violations,
    validate_transactions_can_build_positions,
)
from backend.app.services.positions.helpers.fifo_engine import calculate_fifo_positions
from backend.app.services.transactions.helpers.ingestion import process_transaction_upload
from backend.app.services.transactions.helpers.responses import (
    failure_response,
    success_response,
)
from backend.app.utils.exceptions import (
    DuplicateTransactionError,
    PersistenceError,
)


async def upload_transactions_by_file(
    file: UploadFile,
    db: Session,
) -> TransactionUploadResponse:
    
    '''
    Handles the upload of a transaction file, processes the transactions, updates positions, detects violations, and persists the results.
    - Parameters:
        - file: UploadFile - The file containing the transaction data.
        - db: Session - The database session.
    - Returns:
        - TransactionUploadResponse: An object containing the result of the transaction upload.
    '''

    # Initialize repositories
    transactions = TransactionRepository(db)
    positions = PositionRepository(db)
    violations = ViolationRepository(db)

    # --- VALIDATION AND PROCESSING LOGIC ---
    # Process the uploaded file and extract transaction data
    process_results = await process_transaction_upload(file)

    # If there were errors during process_results, return a failure response with the details
    if process_results.has_errors: 
        return failure_response(process_results)

    # Extract the unique client IDs impacted by the uploaded transactions
    impacted_client_ids = sorted({record.client_id for record in process_results.records})

    try:
        # --- TRANSACTIONAL PERSISTENCE LOGIC ---
        # Persist the new transactions to the database
        transactions.add_records(process_results.records)

        # Retrieve all transactions for the impacted clients, ordered by timestamp and ID
        ordered_transactions = transactions.list_for_clients_ordered(impacted_client_ids)



        # --- POSITION CALCULATION AND PERSISTENCE LOGIC ---
        # Validate that the ordered transactions can be used to build positions
        validate_transactions_can_build_positions(ordered_transactions)

        # Calculate the current positions for the impacted clients based on the ordered transactions
        calculated_positions = calculate_fifo_positions(ordered_transactions)

        # Update the clients' positions in the database with the newly calculated positions
        positions.update_clients_positions(impacted_client_ids, calculated_positions)



        # --- VIOLATION DETECTION AND PERSISTENCE LOGIC ---
        # Build position snapshots for the impacted clients based on the ordered transactions and the calculated positions
        position_snapshots = build_position_snapshots(
            ordered_transactions,
            calculated_positions,
        )
        # Detect violations based on the ordered transactions and the calculated positions
        detected_violations = detect_violations(
            ordered_transactions,
            position_snapshots,
            PERSISTED_RULES,
        )
        violations.update_clients_violations(impacted_client_ids, detected_violations)

        # Commit the changes to the database
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

    return success_response(process_results)
