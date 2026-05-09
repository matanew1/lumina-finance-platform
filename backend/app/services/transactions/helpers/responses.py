from backend.app.schemas.transactions import TransactionUploadResponse
from backend.app.schemas.transactions import TransactionIngestionResult


def failure_response(result: TransactionIngestionResult) -> TransactionUploadResponse:
    return TransactionUploadResponse(
        status="failed",
        total_rows=result.total_rows,
        valid_rows=result.valid_rows,
        invalid_rows=result.invalid_rows,
        persisted_rows=0,
        errors=result.errors,
    )


def success_response(result: TransactionIngestionResult) -> TransactionUploadResponse:
    return TransactionUploadResponse(
        status="success",
        total_rows=result.total_rows,
        valid_rows=result.valid_rows,
        invalid_rows=0,
        persisted_rows=len(result.records),
        errors=[],
    )
