from collections import Counter, defaultdict
from decimal import Decimal

from backend.app.utils.constants import (
    ANALYTICS_CONCENTRATION_THRESHOLD,
    CENT,
    SECONDS_PER_DAY,
    TOP_TRADED_LIMIT,
    ZERO,
)
from backend.app.utils.decimal_utils import percentage
from backend.app.schemas.analytics import (
    AnalyticsResponse,
    ClientAverageHoldingTime,
    HoldingLot,
    IsinConcentrationEntry,
    MostVolatileClient,
    PositionView,
    TopTradedIsin,
    TransactionView,
)


def calculate_top_traded_isins(
    transactions: list[TransactionView],
    limit: int = TOP_TRADED_LIMIT,
) -> list[TopTradedIsin]:
    counts = Counter(sorted(transaction.isin for transaction in transactions))
    return [
        TopTradedIsin(isin=isin, transaction_count=transaction_count)
        for isin, transaction_count in counts.most_common(limit)
    ]


def calculate_average_holding_time_per_client(
    transactions: list[TransactionView],
) -> list[ClientAverageHoldingTime]:
    client_ids = sorted({transaction.client_id for transaction in transactions})
    open_holdings: dict[tuple[str, str], list[HoldingLot]] = defaultdict(list)
    weighted_seconds_by_client: dict[str, Decimal] = defaultdict(lambda: ZERO)
    closed_quantity_by_client: dict[str, Decimal] = defaultdict(lambda: ZERO)

    for transaction in transactions:
        key = (transaction.client_id, transaction.isin)

        if transaction.action == "buy":
            open_holdings[key].append(
                HoldingLot(quantity=transaction.quantity, timestamp=transaction.timestamp)
            )
        elif transaction.action == "sell":
            remaining = transaction.quantity
            while remaining > 0 and open_holdings[key]:
                oldest_holding = open_holdings[key][0]
                consumed = min(oldest_holding.quantity, remaining)
                held_seconds = Decimal(
                    str((transaction.timestamp - oldest_holding.timestamp).total_seconds())
                )

                weighted_seconds_by_client[transaction.client_id] += (
                    held_seconds * consumed
                )
                closed_quantity_by_client[transaction.client_id] += consumed

                oldest_holding.quantity -= consumed
                remaining -= consumed
                if oldest_holding.quantity == 0:
                    open_holdings[key].pop(0)

    return [
        _holding_time_result(
            client_id,
            weighted_seconds_by_client[client_id],
            closed_quantity_by_client[client_id],
        )
        for client_id in client_ids
    ]


def calculate_most_volatile_client(
    transactions: list[TransactionView],
) -> MostVolatileClient | None:
    most_volatile: MostVolatileClient | None = None
    transactions_by_client: dict[str, list[TransactionView]] = defaultdict(list)
    for transaction in transactions:
        transactions_by_client[transaction.client_id].append(transaction)

    for client_id in sorted(transactions_by_client):
        portfolio_values = _portfolio_values_after_each_transaction(
            transactions_by_client[client_id]
        )
        if not portfolio_values:
            continue

        min_value = min(portfolio_values)
        max_value = max(portfolio_values)
        value_range = max_value - min_value
        candidate = MostVolatileClient(
            client_id=client_id,
            min_portfolio_value=min_value,
            max_portfolio_value=max_value,
            value_range=value_range,
        )

        if most_volatile is None or value_range > most_volatile.value_range:
            most_volatile = candidate

    return most_volatile


def calculate_isin_concentration_report(
    transactions: list[TransactionView],
    positions: list[PositionView],
) -> list[IsinConcentrationEntry]:
    total_clients = len({transaction.client_id for transaction in transactions})
    if total_clients == 0:
        return []

    clients_by_isin: dict[str, set[str]] = defaultdict(set)
    for position in positions:
        if position.quantity > 0:
            clients_by_isin[position.isin].add(position.client_id)

    report: list[IsinConcentrationEntry] = []
    for isin, holders in sorted(clients_by_isin.items()):
        clients = sorted(holders)
        client_percentage = percentage(Decimal(len(clients)), Decimal(total_clients))
        if client_percentage > ANALYTICS_CONCENTRATION_THRESHOLD:
            report.append(
                IsinConcentrationEntry(
                    isin=isin,
                    client_count=len(clients),
                    client_percentage=client_percentage,
                    clients=clients,
                )
            )

    return report


def calculate_analytics(
    transactions: list[TransactionView],
    positions: list[PositionView],
) -> AnalyticsResponse:
    return AnalyticsResponse(
        top_traded_isins=ANALYTICS_CALCULATORS["top_traded_isins"](
            transactions,
            positions,
        ),
        average_holding_time_per_client=ANALYTICS_CALCULATORS[
            "average_holding_time_per_client"
        ](transactions, positions),
        most_volatile_client=ANALYTICS_CALCULATORS["most_volatile_client"](
            transactions,
            positions,
        ),
        isin_concentration_report=ANALYTICS_CALCULATORS[
            "isin_concentration_report"
        ](transactions, positions),
    )


def _holding_time_result(
    client_id: str,
    weighted_seconds: Decimal,
    closed_quantity: Decimal,
) -> ClientAverageHoldingTime:
    average_seconds = ZERO if closed_quantity == 0 else weighted_seconds / closed_quantity
    return ClientAverageHoldingTime(
        client_id=client_id,
        average_holding_seconds=average_seconds,
        average_holding_days=(average_seconds / SECONDS_PER_DAY).quantize(CENT),
        closed_quantity=closed_quantity,
    )


def _portfolio_values_after_each_transaction(
    transactions: list[TransactionView],
) -> list[Decimal]:
    quantities: dict[str, Decimal] = defaultdict(lambda: ZERO)
    prices: dict[str, Decimal] = {}
    values: list[Decimal] = []

    for transaction in transactions:
        if transaction.action == "buy":
            quantities[transaction.isin] += transaction.quantity
        elif transaction.action == "sell":
            quantities[transaction.isin] -= transaction.quantity

        prices[transaction.isin] = transaction.price
        values.append(
            sum(
                quantity * prices[isin]
                for isin, quantity in quantities.items()
                if quantity > 0
            )
        )

    return values


ANALYTICS_CALCULATORS = {
    "top_traded_isins": lambda transactions, _positions: calculate_top_traded_isins(
        transactions
    ),
    "average_holding_time_per_client": lambda transactions, _positions: (
        calculate_average_holding_time_per_client(transactions)
    ),
    "most_volatile_client": lambda transactions, _positions: (
        calculate_most_volatile_client(transactions)
    ),
    "isin_concentration_report": calculate_isin_concentration_report,
}
