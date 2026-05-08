from datetime import datetime
from decimal import Decimal
from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator

from backend.schemas.common import OrmSchema


class TransactionBase(OrmSchema):
    client_id: str = Field(examples=["C001"])
    transaction_id: str = Field(examples=["T1001"])
    isin: str = Field(examples=["US1234567890"])
    action: str = Field(examples=["buy"])
    quantity: Decimal = Field(examples=["50"])
    price: Decimal = Field(examples=["100.5"])
    timestamp: datetime = Field(examples=["2023-11-01T10:00:00"])

    @field_validator("action")
    @classmethod
    def validate_action(cls, value: str) -> str:
        normalized = value.strip().lower()
        if normalized not in {"buy", "sell"}:
            raise ValueError("Action must be Buy or Sell.")
        return normalized

    @field_validator("quantity", "price")
    @classmethod
    def validate_positive_decimal(cls, value: Decimal) -> Decimal:
        if value <= 0:
            raise ValueError("Value must be greater than 0.")
        return value


class TransactionRead(TransactionBase):
    id: int


class TransactionUploadError(BaseModel):
    row_number: Optional[int] = Field(default=None, examples=[2])
    field: str = Field(examples=["quantity"])
    message: str = Field(examples=["Quantity must be greater than 0."])
    value: Optional[str] = Field(default=None, examples=["0"])


class TransactionUploadResponse(BaseModel):
    status: Literal["success", "failed"]
    total_rows: int
    valid_rows: int
    invalid_rows: int
    persisted_rows: int
    errors: list[TransactionUploadError] = Field(default_factory=list)
    transactions: list[TransactionBase] = Field(default_factory=list)
