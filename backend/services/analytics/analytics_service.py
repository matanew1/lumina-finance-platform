from collections.abc import Sequence

from sqlalchemy.orm import Session

from backend.db.repositories.analytics_repository import AnalyticsRepository
from backend.services.analytics.calculators import (
    AnalyticsCalculator,
    AverageHoldingTimeCalculator,
    IsinConcentrationCalculator,
    MostVolatileClientCalculator,
    TopTradedIsinsCalculator,
)


class AnalyticsService:
    def __init__(
        self,
        db: Session,
        analytics_repository: AnalyticsRepository | None = None,
        calculators: Sequence[AnalyticsCalculator] | None = None,
    ) -> None:
        self.analytics_repository = analytics_repository or AnalyticsRepository(db)
        self.calculators = list(calculators or self._default_calculators())

    def get_analytics(self) -> dict:
        transactions = self.analytics_repository.list_transactions_ordered()
        positions = self.analytics_repository.list_current_positions()

        return {
            calculator.report_name: calculator.calculate(transactions, positions)
            for calculator in self.calculators
        }

    @staticmethod
    def _default_calculators() -> list[AnalyticsCalculator]:
        return [
            TopTradedIsinsCalculator(),
            AverageHoldingTimeCalculator(),
            MostVolatileClientCalculator(),
            IsinConcentrationCalculator(),
        ]
