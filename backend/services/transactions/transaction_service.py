from fastapi import UploadFile
from sqlalchemy.orm import Session

from backend.db.repositories.transaction_repository import TransactionRepository
from backend.services.transactions.transaction_ingestion import (
    normalize_transaction_dataframe,
    read_transaction_excel,
    transaction_records_from_dataframe,
    validate_transaction_dataframe,
)


class TransactionService:
    def __init__(self, db: Session) -> None:
        self.transaction_repository = TransactionRepository(db)

    async def upload_transactions(self, file: UploadFile):
        dataframe = await read_transaction_excel(file)
        normalized = normalize_transaction_dataframe(dataframe)
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
                "transactions": [],
            }

        records = transaction_records_from_dataframe(normalized)
        self.transaction_repository.bulk_create(records)

        return {
            "status": "success",
            "total_rows": total_rows,
            "valid_rows": total_rows,
            "invalid_rows": 0,
            "persisted_rows": len(records),
            "errors": [],
            "transactions": records,
        }
