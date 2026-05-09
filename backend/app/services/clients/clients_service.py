from typing import Protocol

from backend.app.api.schemas.clients import ClientResponse


def list_clients(repository) -> list[ClientResponse]:
    return [
        ClientResponse(client_id=client_id)
        for client_id in repository.list_client_ids()
    ]
