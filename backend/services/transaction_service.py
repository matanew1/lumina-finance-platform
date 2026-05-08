from fastapi import UploadFile
from sqlalchemy.orm import Session


class TransactionService:
    def __init__(self, db: Session) -> None:
        self.db = db

    async def upload_transactions(self, file: UploadFile):
        # TODO: parse Excel with pandas, validate rows, persist transactions, positions, and violations.
        raise NotImplementedError("TODO: implement transaction upload service.")
