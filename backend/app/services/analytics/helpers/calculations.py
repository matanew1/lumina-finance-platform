from backend.app.schemas.analytics import (
    AnalyticsResponse,
    PositionView,
    TransactionView,
)
from backend.app.services.analytics.helpers.concentration import (
    calculate_isin_concentration_report,
)
from backend.app.services.analytics.helpers.holding_time import (
    calculate_average_holding_time_per_client,
)
from backend.app.services.analytics.helpers.top_traded import calculate_top_traded_isins
from backend.app.services.analytics.helpers.volatility import (
    calculate_most_volatile_client,
)


def calculate_analytics(
    transactions: list[TransactionView],
    positions: list[PositionView],
) -> AnalyticsResponse:
    return AnalyticsResponse(
        top_traded_isins=calculate_top_traded_isins(transactions),
        average_holding_time_per_client=calculate_average_holding_time_per_client(
            transactions
        ),
        most_volatile_client=calculate_most_volatile_client(transactions),
        isin_concentration_report=calculate_isin_concentration_report(
            transactions,
            positions,
        ),
    )
