from fastapi import APIRouter, Depends, File, UploadFile, status
from sqlalchemy.orm import Session

from backend.app.db.session import get_db
from backend.app.schemas.transactions import TransactionUploadResponse
from backend.app.services.transactions.transactions_service import upload_transactions_by_file

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
    '''
    Uploads a file containing transaction data and processes it.
    - Parameters:
        - file: UploadFile - The file containing the transaction data.
        - db: Session - The database session.
    - Returns:
        - TransactionUploadResponse: An object containing the result of the transaction upload.
    '''
    return await upload_transactions_by_file(file=file, db=db)
