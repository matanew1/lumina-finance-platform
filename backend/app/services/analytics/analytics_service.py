from backend.app.api.schemas.analytics import AnalyticsResponse
from backend.app.services.analytics.helpers.calculations import calculate_analytics


def get_analytics(repository) -> AnalyticsResponse:
    transactions = repository.list_transactions_ordered()
    positions = repository.list_current_positions()
    result = calculate_analytics(transactions, positions)
    return AnalyticsResponse.model_validate(result.model_dump())
