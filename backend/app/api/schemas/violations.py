from datetime import datetime

from pydantic import BaseModel, ConfigDict

# Main Violation Response Model
class ViolationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    client_id: str
    transaction_id: str | None = None
    violation_type: str
    severity: str
    message: str
    created_at: datetime
