from datetime import datetime
from decimal import Decimal

from pydantic import Field

from backend.schemas.common import OrmSchema


class PositionRead(OrmSchema):
    id: int
    client_id: str = Field(examples=["C001"])
    isin: str = Field(examples=["US1234567890"])
    quantity: Decimal = Field(examples=["30"])
    average_price: Decimal = Field(examples=["100.5"])
    updated_at: datetime

    # TODO: align this schema with stored-versus-computed position decisions.
