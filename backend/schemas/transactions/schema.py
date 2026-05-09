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
