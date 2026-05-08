from datetime import datetime
from typing import Optional

from pydantic import Field

from backend.schemas.common import OrmSchema


class ViolationRead(OrmSchema):
    id: int
    client_id: str = Field(examples=["C001"])
    transaction_id: Optional[str] = Field(default=None, examples=["T1002"])
    violation_type: str = Field(examples=["negative_position"])
    message: str
    created_at: datetime

    # TODO: add severity, status, and remediation fields once compliance rules are defined.
