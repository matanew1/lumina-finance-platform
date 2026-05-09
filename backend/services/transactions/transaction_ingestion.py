from fastapi import UploadFile

from backend.services.transactions.types import TransactionIngestionResult
from backend.utils.transactions.ingestion import (
    normalize_transaction_dataframe,
    read_transaction_file,
    transaction_records_from_dataframe,
    validate_transaction_dataframe,
)


class TransactionIngestionService:
    async def read_normalized_records(self, file: UploadFile) -> TransactionIngestionResult:
        dataframe = await read_transaction_file(file)
        normalized = normalize_transaction_dataframe(dataframe)
        errors = validate_transaction_dataframe(normalized)

        total_rows = len(normalized)
        invalid_rows = len(
            {error["row_number"] for error in errors if error["row_number"] is not None}
        )
        valid_rows = total_rows - invalid_rows

        if errors:
            return TransactionIngestionResult(
                total_rows=total_rows,
                valid_rows=valid_rows,
                invalid_rows=invalid_rows,
                errors=errors,
            )

        return TransactionIngestionResult(
            records=transaction_records_from_dataframe(normalized),
            total_rows=total_rows,
            valid_rows=valid_rows,
            invalid_rows=0,
            errors=[],
        )
