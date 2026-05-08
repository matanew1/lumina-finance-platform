from datetime import datetime
from decimal import Decimal

from pydantic import Field

from backend.schemas.common import OrmSchema


class TransactionBase(OrmSchema):
    client_id: str = Field(examples=["C001"])
    transaction_id: str = Field(examples=["T1001"])
    isin: str = Field(examples=["US1234567890"])
    action: str = Field(examples=["buy"])
    quantity: Decimal = Field(examples=["50"])
    price: Decimal = Field(examples=["100.5"])
    timestamp: datetime = Field(examples=["2023-11-01T10:00:00"])

    # TODO: add strict validation for action values, ISIN format, and numeric ranges.


class TransactionRead(TransactionBase):
    id: int
