from pydantic import BaseModel, ConfigDict


# Main Clients Response Model
class ClientResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    client_id: str
