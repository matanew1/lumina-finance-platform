from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from backend.db.repositories.analytics.repository import AnalyticsRepository
from backend.db.database import get_db
from backend.schemas.analytics.schema import AnalyticsResponse
from backend.services.analytics.analytics_service import AnalyticsService

router = APIRouter(tags=["analytics"])


def get_analytics_service(db: Session = Depends(get_db)) -> AnalyticsService:
    return AnalyticsService(analytics_repository=AnalyticsRepository(db))


@router.get("/analytics", response_model=AnalyticsResponse, status_code=status.HTTP_200_OK)
def get_analytics(service: AnalyticsService = Depends(get_analytics_service)) -> AnalyticsResponse:
    return AnalyticsResponse.model_validate(service.get_analytics())
