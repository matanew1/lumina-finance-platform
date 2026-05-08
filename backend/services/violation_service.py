from sqlalchemy.orm import Session


class ViolationService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_violations(self):
        # TODO: query compliance/business-rule violations.
        raise NotImplementedError("TODO: implement violations service.")
