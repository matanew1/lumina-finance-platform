from fastapi import UploadFile

from backend.app.services.shared.csv_handler import read_transaction_file
from backend.app.services.transactions.helpers.dataframe import (
    normalize_transaction_dataframe,
    transaction_records_from_dataframe,
    validate_transaction_dataframe,
)
from backend.app.services.transactions.schemas import TransactionIngestionResult


async def process_transaction_upload(file: UploadFile) -> TransactionIngestionResult:
    dataframe = await read_transaction_file(file)
    normalized = normalize_transaction_dataframe(dataframe)
    errors = validate_transaction_dataframe(normalized)

    total_rows = len(normalized)
    invalid_rows = len(
        {error.row_number for error in errors if error.row_number is not None}
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
