from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field

from backend.app.api.schemas.transactions import TransactionUploadError


class TransactionIngested(BaseModel):
    client_id: str = Field(min_length=1)
    transaction_id: str = Field(min_length=1)
    isin: str = Field(min_length=1)
    action: Literal["buy", "sell"]
    quantity: Decimal = Field(gt=0)
    price: Decimal = Field(gt=0)
    timestamp: datetime


class TransactionIngestionResult(BaseModel):
    records: list[TransactionIngested] = Field(default_factory=list)
    total_rows: int = 0
    valid_rows: int = 0
    invalid_rows: int = 0
    errors: list[TransactionUploadError] = Field(default_factory=list)

    @property
    def has_errors(self) -> bool:
        return bool(self.errors)
