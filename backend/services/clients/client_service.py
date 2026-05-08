from sqlalchemy.orm import Session

from backend.db.repositories.client_repository import ClientRepository


class ClientService:
    def __init__(
        self,
        db: Session,
        client_repository: ClientRepository | None = None,
    ) -> None:
        self.client_repository = client_repository or ClientRepository(db)

    def get_clients(self) -> list[dict[str, str]]:
        client_ids = self.client_repository.list_client_ids()
        return [{"client_id": client_id} for client_id in client_ids]
