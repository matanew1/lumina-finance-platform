from collections import Counter, defaultdict, deque
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Any

from backend.services.analytics.constants import (
    CONCENTRATION_THRESHOLD,
    PERCENT,
    SECONDS_PER_DAY,
    TOP_TRADED_LIMIT,
    ZERO,
)


class TopTradedIsinsCalculator:
    report_name = "top_traded_isins"

    def __init__(self, limit: int = TOP_TRADED_LIMIT) -> None:
        self.limit = limit

    def calculate(self, transactions: list[Any], positions: list[Any]) -> list[dict]:
        counts = Counter(transaction.isin for transaction in transactions)
        ranked = sorted(counts.items(), key=lambda item: (-item[1], item[0]))[: self.limit]
        return [
            {"isin": isin, "transaction_count": transaction_count}
            for isin, transaction_count in ranked
        ]


@dataclass
class OpenHolding:
    quantity: Decimal
    timestamp: datetime


class AverageHoldingTimeCalculator:
    report_name = "average_holding_time_per_client"

    def calculate(self, transactions: list[Any], positions: list[Any]) -> list[dict]:
        client_ids = sorted({transaction.client_id for transaction in transactions})
        open_holdings: dict[tuple[str, str], deque[OpenHolding]] = defaultdict(deque)
        weighted_seconds_by_client: dict[str, Decimal] = defaultdict(lambda: ZERO)
        closed_quantity_by_client: dict[str, Decimal] = defaultdict(lambda: ZERO)

        for transaction in transactions:
            key = (transaction.client_id, transaction.isin)

            if transaction.action == "buy":
                open_holdings[key].append(
                    OpenHolding(
                        quantity=transaction.quantity,
                        timestamp=transaction.timestamp,
                    )
                )
                continue

            if transaction.action == "sell":
                self._apply_sell(
                    transaction=transaction,
                    open_holdings=open_holdings[key],
                    weighted_seconds_by_client=weighted_seconds_by_client,
                    closed_quantity_by_client=closed_quantity_by_client,
                )

        return [
            self._build_client_result(
                client_id=client_id,
                weighted_seconds=weighted_seconds_by_client[client_id],
                closed_quantity=closed_quantity_by_client[client_id],
            )
            for client_id in client_ids
        ]

    @staticmethod
    def _apply_sell(
        transaction: Any,
        open_holdings: deque[OpenHolding],
        weighted_seconds_by_client: dict[str, Decimal],
        closed_quantity_by_client: dict[str, Decimal],
    ) -> None:
        remaining = transaction.quantity

        while remaining > 0 and open_holdings:
            oldest_holding = open_holdings[0]
            consumed = min(oldest_holding.quantity, remaining)
            held_seconds = Decimal(str((transaction.timestamp - oldest_holding.timestamp).total_seconds()))

            weighted_seconds_by_client[transaction.client_id] += held_seconds * consumed
            closed_quantity_by_client[transaction.client_id] += consumed

            oldest_holding.quantity -= consumed
            remaining -= consumed
            if oldest_holding.quantity == 0:
                open_holdings.popleft()

    @staticmethod
    def _build_client_result(
        client_id: str,
        weighted_seconds: Decimal,
        closed_quantity: Decimal,
    ) -> dict:
        average_seconds = ZERO
        if closed_quantity > 0:
            average_seconds = weighted_seconds / closed_quantity

        return {
            "client_id": client_id,
            "average_holding_seconds": average_seconds,
            "average_holding_days": (average_seconds / SECONDS_PER_DAY).quantize(Decimal("0.01")),
            "closed_quantity": closed_quantity,
        }


class MostVolatileClientCalculator:
    report_name = "most_volatile_client"

    def calculate(self, transactions: list[Any], positions: list[Any]) -> dict | None:
        transactions_by_client = self._group_transactions_by_client(transactions)

        most_volatile: dict | None = None
        for client_id in sorted(transactions_by_client):
            portfolio_values = self._portfolio_values_after_each_transaction(transactions_by_client[client_id])
            if not portfolio_values:
                continue

            min_value = min(portfolio_values)
            max_value = max(portfolio_values)
            value_range = max_value - min_value
            candidate = {
                "client_id": client_id,
                "min_portfolio_value": min_value,
                "max_portfolio_value": max_value,
                "value_range": value_range,
            }

            if most_volatile is None or value_range > most_volatile["value_range"]:
                most_volatile = candidate

        return most_volatile

    @staticmethod
    def _group_transactions_by_client(transactions: list[Any]) -> dict[str, list[Any]]:
        transactions_by_client: dict[str, list[Any]] = defaultdict(list)
        for transaction in transactions:
            transactions_by_client[transaction.client_id].append(transaction)
        return transactions_by_client

    @staticmethod
    def _portfolio_values_after_each_transaction(transactions: list[Any]) -> list[Decimal]:
        quantities: dict[str, Decimal] = defaultdict(lambda: ZERO)
        prices: dict[str, Decimal] = {}
        portfolio_values: list[Decimal] = []

        for transaction in transactions:
            if transaction.action == "buy":
                quantities[transaction.isin] += transaction.quantity
            elif transaction.action == "sell":
                quantities[transaction.isin] -= transaction.quantity

            prices[transaction.isin] = transaction.price
            portfolio_values.append(
                sum(
                    quantity * prices[isin]
                    for isin, quantity in quantities.items()
                    if quantity > 0
                )
            )

        return portfolio_values


class IsinConcentrationCalculator:
    report_name = "isin_concentration_report"

    def __init__(self, threshold: Decimal = CONCENTRATION_THRESHOLD) -> None:
        self.threshold = threshold

    def calculate(self, transactions: list[Any], positions: list[Any]) -> list[dict]:
        total_clients = len({transaction.client_id for transaction in transactions})
        if total_clients == 0:
            return []

        clients_by_isin = self._clients_by_isin(positions)

        report = []
        for isin in sorted(clients_by_isin):
            clients = sorted(clients_by_isin[isin])
            client_percentage = (Decimal(len(clients)) / Decimal(total_clients) * PERCENT).quantize(Decimal("0.01"))
            if client_percentage > self.threshold:
                report.append(
                    {
                        "isin": isin,
                        "client_count": len(clients),
                        "client_percentage": client_percentage,
                        "clients": clients,
                    }
                )

        return report

    @staticmethod
    def _clients_by_isin(positions: list[Any]) -> dict[str, set[str]]:
        clients_by_isin: dict[str, set[str]] = defaultdict(set)
        for position in positions:
            if position.quantity > 0:
                clients_by_isin[position.isin].add(position.client_id)
        return clients_by_isin
