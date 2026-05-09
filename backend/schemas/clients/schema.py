from pydantic import BaseModel


class ClientResponse(BaseModel):
    client_id: str
