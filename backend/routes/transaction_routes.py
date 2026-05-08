from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.orm import Session

from backend.controller.transaction_controller import TransactionController
from backend.db.session import get_db
from backend.schemas.common import TODO_RESPONSES

router = APIRouter(tags=["transactions"])


def get_transaction_controller(db: Session = Depends(get_db)) -> TransactionController:
    return TransactionController(db=db)


@router.post("/upload-transactions", responses=TODO_RESPONSES)
async def upload_transactions(
    file: UploadFile = File(...),
    controller: TransactionController = Depends(get_transaction_controller),
):
    # TODO: validate upload metadata and delegate the parsing workflow.
    return await controller.upload_transactions(file)
