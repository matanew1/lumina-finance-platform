from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field


class TransactionUploadError(BaseModel):
    row_number: int | None = None
    field: str
    message: str
    value: str | None = None


class TransactionUploadResponse(BaseModel):
    status: Literal["success", "failed"]
    total_rows: int
    valid_rows: int
    invalid_rows: int
    persisted_rows: int
    errors: list[TransactionUploadError] = Field(default_factory=list)


class TransactionIngested(BaseModel):
    client_id: str = Field(min_length=1)
    transaction_id: str = Field(min_length=1)
    isin: str = Field(min_length=1)
    action: Literal["buy", "sell"]
    quantity: Decimal = Field(gt=0)
    price: Decimal = Field(gt=0)
    timestamp: datetime


class TransactionIngestionResult(BaseModel):
    '''
    Represents the result of ingesting a batch of transactions, including the successfully ingested records, counts of total/valid/invalid rows, and any errors encountered during validation.
    - Attributes:
        - records: list[TransactionIngested] - A list of successfully ingested transaction records. This will be empty if there were validation errors.
        - total_rows: int - The total number of rows processed from the uploaded file.
        - valid_rows: int - The number of rows that were successfully validated and ingested.
        - invalid_rows: int - The number of rows that failed validation.
        - errors: list[TransactionUploadError] - A list of errors encountered during validation, including details about the specific issues with each invalid row.
    '''
    records: list[TransactionIngested] = Field(default_factory=list)
    total_rows: int = 0
    valid_rows: int = 0
    invalid_rows: int = 0
    errors: list[TransactionUploadError] = Field(default_factory=list)

    @property
    def has_errors(self) -> bool:
        return bool(self.errors)
