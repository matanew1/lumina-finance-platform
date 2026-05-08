from datetime import datetime
from typing import Optional

from pydantic import Field

from backend.schemas.common import OrmSchema


class ViolationRead(OrmSchema):
    id: int
    client_id: str = Field(examples=["C001"])
    transaction_id: Optional[str] = Field(default=None, examples=["T1002"])
    violation_type: str = Field(examples=["DAY_TRADING"])
    severity: str = Field(examples=["WARNING"])
    message: str = Field(examples=["4 buy/sell pairs of US1234567890 within 24h (limit: 3)."])
    created_at: datetime
