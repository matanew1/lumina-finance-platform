from fastapi import APIRouter, Depends, File, HTTPException, status, UploadFile
from sqlalchemy.orm import Session

from backend.db.database import get_db
from backend.db.repositories.positions.repository import PositionRepository
from backend.db.repositories.transactions.repository import TransactionRepository
from backend.db.repositories.violations.repository import ViolationRepository
from backend.schemas.transactions.schema import TransactionUploadResponse
from backend.services.positions.position_service import PositionService
from backend.services.transactions.transaction_service import TransactionService
from backend.services.violations.violation_service import ViolationService
from backend.utils.errors.exceptions import BadRequestError, ConflictError, PersistenceError

router = APIRouter(tags=["transactions"])


def get_transaction_service(db: Session = Depends(get_db)) -> TransactionService:
    position_service = PositionService(position_repository=PositionRepository(db))
    violation_service = ViolationService(violation_repository=ViolationRepository(db))
    return TransactionService(
        transaction_repository=TransactionRepository(db),
        position_service=position_service,
        violation_service=violation_service,
        db=db,
    )


@router.post(
    "/upload-transactions",
    response_model=TransactionUploadResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_transactions(
    file: UploadFile = File(...),
    service: TransactionService = Depends(get_transaction_service),
):
    try:
        return await service.upload_transactions(file=file)
    except ConflictError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except BadRequestError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except PersistenceError as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc
