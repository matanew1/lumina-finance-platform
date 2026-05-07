from typing import Optional

from pydantic import BaseModel, ConfigDict


class OrmSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class TodoResponse(BaseModel):
    status: str
    message: str
    endpoint: Optional[str] = None

TODO_RESPONSES = {
    501: {
        "model": TodoResponse,
        "description": "Endpoint registered, implementation intentionally left as TODO.",
    }
}