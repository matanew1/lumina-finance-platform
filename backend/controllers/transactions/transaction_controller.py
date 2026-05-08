from fastapi import APIRouter, Depends, File, HTTPException, status, UploadFile
from sqlalchemy.orm import Session

from backend.db.session import get_db
from backend.schemas.transaction_schema import TransactionUploadResponse
from backend.services.transactions.transaction_service import TransactionService
from backend.utils.exceptions import ConflictError, PersistenceError, BadRequestError

router = APIRouter(tags=["transactions"])


class TransactionController:
    def __init__(self, db: Session) -> None:
        self.service = TransactionService(db=db)

    async def upload_transactions(self, file: UploadFile):
        try:
            return await self.service.upload_transactions(file=file)
        except ConflictError as exc:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
        except BadRequestError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
        except PersistenceError as exc:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc


def get_transaction_controller(db: Session = Depends(get_db)) -> TransactionController:
    return TransactionController(db=db)


@router.post(
    "/upload-transactions",
    response_model=TransactionUploadResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_transactions(
    file: UploadFile = File(...),
    controller: TransactionController = Depends(get_transaction_controller),
):
    return await controller.upload_transactions(file)
