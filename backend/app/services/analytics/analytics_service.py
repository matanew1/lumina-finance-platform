from typing import Protocol

from backend.app.schemas.analytics import (
    AnalyticsResponse,
    PositionView,
    TransactionView,
)
from backend.app.services.analytics.helpers.calculations import calculate_analytics


class AnalyticsRepositoryProtocol(Protocol):
    def list_transactions_ordered(self) -> list[TransactionView]: ...
    def list_current_positions(self) -> list[PositionView]: ...


def get_analytics(repository: AnalyticsRepositoryProtocol) -> AnalyticsResponse:
    transactions = repository.list_transactions_ordered()
    positions = repository.list_current_positions()
    return calculate_analytics(transactions, positions)
