from backend.db.repositories.analytics.repository import AnalyticsRepository
from backend.services.analytics.reports import AnalyticsReports
from backend.services.analytics.types import AnalyticsResponse


class AnalyticsService:
    def __init__(
        self,
        analytics_repository: AnalyticsRepository,
        reports: AnalyticsReports | None = None,
    ) -> None:
        self.analytics_repository = analytics_repository
        self.reports = reports or AnalyticsReports()

    def get_analytics(self) -> AnalyticsResponse:
        transactions = self.analytics_repository.list_transactions_ordered()
        positions = self.analytics_repository.list_current_positions()

        return {
            "top_traded_isins": self.reports.top_traded_isins(transactions),
            "average_holding_time_per_client": self.reports.average_holding_time_per_client(
                transactions
            ),
            "most_volatile_client": self.reports.most_volatile_client(transactions),
            "isin_concentration_report": self.reports.isin_concentration_report(
                transactions,
                positions,
            ),
        }
