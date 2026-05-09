from fastapi import APIRouter, Depends, File, UploadFile, status
from sqlalchemy.orm import Session

from backend.app.db.session import get_db
from backend.app.api.schemas.transactions import TransactionUploadResponse
from backend.app.services.transactions.transactions_service import (
    upload_transactions as upload_use_case,
)

router = APIRouter(tags=["transactions"])


@router.post(
    "/upload-transactions",
    response_model=TransactionUploadResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_transactions(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> TransactionUploadResponse:
    return await upload_use_case(file=file, db=db)
