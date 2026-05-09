from backend.app.services.analytics.helpers.calculations import calculate_analytics
from backend.app.schemas.analytics import AnalyticsResponse


def get_analytics(repository) -> AnalyticsResponse:
    transactions = repository.list_transactions_ordered()
    positions = repository.list_current_positions()
    return calculate_analytics(transactions, positions)
