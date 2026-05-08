from sqlalchemy.orm import Session


class ClientService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_clients(self):
        # TODO: query distinct clients from transaction and position data.
        raise NotImplementedError("TODO: implement client listing service.")
