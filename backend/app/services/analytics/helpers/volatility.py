from collections import defaultdict
from decimal import Decimal

from backend.app.schemas.analytics import MostVolatileClient, TransactionView
from backend.app.utils.constants import ZERO


def calculate_most_volatile_client(
    transactions: list[TransactionView],
) -> MostVolatileClient | None:
    candidates = (
        _client_volatility(client_id, client_transactions)
        for client_id, client_transactions in sorted(
            _transactions_by_client(transactions).items()
        )
    )
    return max(candidates, key=lambda candidate: candidate.value_range, default=None)


def _transactions_by_client(
    transactions: list[TransactionView],
) -> dict[str, list[TransactionView]]:
    grouped: dict[str, list[TransactionView]] = defaultdict(list)
    for transaction in transactions:
        grouped[transaction.client_id].append(transaction)
    return grouped


def _client_volatility(
    client_id: str,
    transactions: list[TransactionView],
) -> MostVolatileClient:
    quantities: dict[str, Decimal] = defaultdict(lambda: ZERO)
    prices: dict[str, Decimal] = {}
    min_value: Decimal | None = None
    max_value: Decimal | None = None

    for transaction in transactions:
        if transaction.action == "buy":
            quantities[transaction.isin] += transaction.quantity
        elif transaction.action == "sell":
            quantities[transaction.isin] -= transaction.quantity

        prices[transaction.isin] = transaction.price
        portfolio_value = _portfolio_value(quantities, prices)
        min_value = (
            portfolio_value if min_value is None else min(min_value, portfolio_value)
        )
        max_value = (
            portfolio_value if max_value is None else max(max_value, portfolio_value)
        )

    min_value = min_value or ZERO
    max_value = max_value or ZERO
    return MostVolatileClient(
        client_id=client_id,
        min_portfolio_value=min_value,
        max_portfolio_value=max_value,
        value_range=max_value - min_value,
    )


def _portfolio_value(
    quantities: dict[str, Decimal],
    prices: dict[str, Decimal],
) -> Decimal:
    return sum(
        quantity * prices[isin]
        for isin, quantity in quantities.items()
        if quantity > 0
    )
