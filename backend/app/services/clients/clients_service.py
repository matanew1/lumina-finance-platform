from typing import Protocol

from backend.app.schemas.clients import ClientResponse
from backend.app.repositories.clients import ClientRepository


def list_clients(repository: ClientRepository) -> list[ClientResponse]:
    '''
    Lists all clients.
    - Parameters:
        - repository: ClientRepository - The client repository instance.
    - Returns:
        - list[ClientResponse]: A list of ClientResponse objects, each containing a client_id.
    '''
    return [
        ClientResponse(client_id=client_id)
        for client_id in repository.list_client_ids()
    ]
