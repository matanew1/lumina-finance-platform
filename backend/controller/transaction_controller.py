from fastapi import UploadFile
from sqlalchemy.orm import Session

from backend.services.transaction_service import TransactionService
from backend.utils.responses import todo_response


class TransactionController:
    def __init__(self, db: Session) -> None:
        self.service = TransactionService(db=db)

    async def upload_transactions(self, file: UploadFile):
        # TODO: add request-level validation before calling the service.
        try:
            return await self.service.upload_transactions(file=file)
        except NotImplementedError as exc:
            return todo_response(str(exc), endpoint="POST /upload-transactions")
