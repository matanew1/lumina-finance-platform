from sqlalchemy.orm import Session


class PositionService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_client_positions(self, client_id: str):
        # TODO: compute or query positions for the requested client.
        raise NotImplementedError("TODO: implement client positions service.")
