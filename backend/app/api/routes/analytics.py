from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from backend.app.db.session import get_db
from backend.app.repositories.analytics import AnalyticsRepository
from backend.app.schemas.analytics import AnalyticsResponse
from backend.app.services.analytics.analytics_service import (
    get_analytics as get_analytics_use_case,
)

router = APIRouter(tags=["analytics"])


@router.get(
    "/analytics",
    response_model=AnalyticsResponse,
    status_code=status.HTTP_200_OK,
)
def get_analytics(db: Session = Depends(get_db)) -> AnalyticsResponse:
    return get_analytics_use_case(AnalyticsRepository(db))
