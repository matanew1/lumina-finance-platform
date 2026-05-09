from fastapi import UploadFile

from backend.app.utils.files import read_table_from_file
from backend.app.services.transactions.helpers.dataframe import (
    normalize_transaction_dataframe,
    transaction_records_from_dataframe,
    validate_transaction_dataframe,
)
from backend.app.schemas.transactions import TransactionIngestionResult


async def process_transaction_upload(file: UploadFile) -> TransactionIngestionResult:
    '''
    Processes the uploaded transaction file, normalizes and validates the data, and returns the results.
    - Parameters:
        - file: UploadFile - The file containing the transaction data.
    - Returns:
        - TransactionIngestionResult: An object containing the results of the ingestion process, including any errors encountered.
    '''
    # Read the transaction file and load it into a DataFrame
    dataframe = await read_table_from_file(file)

    # Normalize the DataFrame
    normalized = normalize_transaction_dataframe(dataframe)

    # Validate the normalized DataFrame and collect any errors
    errors = validate_transaction_dataframe(normalized)

    # Calculate the total number of rows, valid rows, and invalid rows
    total_rows = len(normalized)
    invalid_rows = len(
        {error.row_number for error in errors if error.row_number is not None}
    )
    valid_rows = total_rows - invalid_rows

    # If there were errors during validation, return a result containing the error details
    if errors:
        return TransactionIngestionResult(
            total_rows=total_rows,
            valid_rows=valid_rows,
            invalid_rows=invalid_rows,
            errors=errors,
        )

    # If there were no errors, convert the normalized DataFrame into a list of transaction records and return a successful result
    return TransactionIngestionResult(
        records=transaction_records_from_dataframe(normalized),
        total_rows=total_rows,
        valid_rows=valid_rows,
        invalid_rows=0,
        errors=[],
    )
