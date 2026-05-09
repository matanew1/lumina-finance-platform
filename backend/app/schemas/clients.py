from pydantic import BaseModel, ConfigDict


# Main Clients Response Model
class ClientResponse(BaseModel):
    '''
    A schema for representing a client response.

    Attributes:
        client_id (str): The ID of the client.
    '''
    model_config = ConfigDict(from_attributes=True) # Enable parsing from ORM objects

    client_id: str
