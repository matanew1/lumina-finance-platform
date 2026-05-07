from sqlalchemy.orm import Session

from backend.services.client_service import ClientService
from backend.utils.responses import todo_response


class ClientController:
    def __init__(self, db: Session) -> None:
        self.service = ClientService(db=db)

    def get_clients(self):
        # TODO: add request parameters and response mapping.
        try:
            return self.service.get_clients()
        except NotImplementedError as exc:
            return todo_response(str(exc), endpoint="GET /clients")
