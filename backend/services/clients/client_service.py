from backend.db.repositories.clients.repository import ClientRepository
from backend.services.clients.types import ClientResponse


class ClientService:
    def __init__(self, client_repository: ClientRepository) -> None:
        self.client_repository = client_repository

    def get_clients(self) -> list[dict[str, str]]:
        client_ids = self.client_repository.list_client_ids()
        return [ClientResponse(client_id=client_id).as_dict() for client_id in client_ids]
