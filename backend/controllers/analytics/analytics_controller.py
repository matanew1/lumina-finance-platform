from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from backend.db.session import get_db
from backend.schemas.analytics_schema import AnalyticsRead
from backend.services.analytics.analytics_service import AnalyticsService

router = APIRouter(tags=["analytics"])


def get_analytics_service(db: Session = Depends(get_db)) -> AnalyticsService:
    return AnalyticsService(db=db)


@router.get("/analytics", response_model=AnalyticsRead, status_code=status.HTTP_200_OK)
def get_analytics(service: AnalyticsService = Depends(get_analytics_service)) -> AnalyticsRead:
    return AnalyticsRead.model_validate(service.get_analytics())
