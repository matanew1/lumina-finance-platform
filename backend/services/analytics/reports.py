from collections import Counter, defaultdict, deque
from decimal import Decimal

from backend.services.analytics.types import HoldingLot, PositionView, ReportRow, TransactionView

'''
Description:
This module provides functions to generate various analytical reports based on transaction data. The reports include:
1. Top Traded ISINs: Identifies the most frequently traded ISINs based on transaction counts.
2. Average Holding Time per Client: Calculates the average time clients hold their positions before selling.
3. Most Volatile Portfolio: Determines which client's portfolio has the largest value range over time.
4. ISIN Concentration Report: Identifies ISINs that are held by a disproportionately high percentage of clients, indicating potential concentration risk.

Logic:
1. For the Top Traded ISINs report, we count the occurrences of each ISIN in the transactions and rank them by count.
2. For the Average Holding Time report, we track open holdings for each client and calculate the weighted average holding time when positions are closed.
3. For the Most Volatile Portfolio report, we calculate the portfolio value after each transaction for each client and determine the range of values to identify volatility.
4. For the ISIN Concentration Report, we count the number of unique clients holding each ISIN and calculate the percentage of total clients to identify high
'''


# Constants and type aliases for better readability
SECONDS_PER_DAY = Decimal("86400")
PERCENT = Decimal("100")
CONCENTRATION_THRESHOLD = Decimal("70.00")
TOP_TRADED_LIMIT = 3
ZERO = Decimal("0")


class AnalyticsReports:
    # Report 1: Top Traded ISINs
    def top_traded_isins(
        self,
        transactions: list[TransactionView],
        limit: int = TOP_TRADED_LIMIT,
    ) -> list[ReportRow]:
        counts = Counter(transaction.isin for transaction in transactions)
        ranked = sorted(counts.items(), key=lambda item: (-item[1], item[0]))[:limit]
        return [
            {"isin": isin, "transaction_count": transaction_count}
            for isin, transaction_count in ranked
        ]

    # Report 2: Average Holding Time per Client
    def average_holding_time_per_client(
        self,
        transactions: list[TransactionView],
    ) -> list[ReportRow]:
        client_ids = sorted({transaction.client_id for transaction in transactions})
        open_holdings: dict[tuple[str, str], deque[HoldingLot]] = defaultdict(deque)
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
                        str(
                            (transaction.timestamp - oldest_holding.timestamp).total_seconds()
                        )
                    )

                    weighted_seconds_by_client[transaction.client_id] += held_seconds * consumed
                    closed_quantity_by_client[transaction.client_id] += consumed

                    oldest_holding.quantity -= consumed
                    remaining -= consumed
                    if oldest_holding.quantity == 0:
                        open_holdings[key].popleft()

        return [
            self._holding_time_result(
                client_id,
                weighted_seconds_by_client[client_id],
                closed_quantity_by_client[client_id],
            )
            for client_id in client_ids
        ]

    # Report 3: Most Volatile Portfolio
    def most_volatile_client(
        self,
        transactions: list[TransactionView],
    ) -> ReportRow | None:
        most_volatile: ReportRow | None = None
        transactions_by_client: dict[str, list[TransactionView]] = defaultdict(list)
        for transaction in transactions:
            transactions_by_client[transaction.client_id].append(transaction)

        for client_id in sorted(transactions_by_client):
            portfolio_values = self._portfolio_values_after_each_transaction(
                transactions_by_client[client_id]
            )
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

    # Report 4: ISIN Concentration Report
    def isin_concentration_report(
        self,
        transactions: list[TransactionView],
        positions: list[PositionView],
    ) -> list[ReportRow]:
        total_clients = len({transaction.client_id for transaction in transactions})
        if total_clients == 0:
            return []

        clients_by_isin: dict[str, set[str]] = defaultdict(set)
        for position in positions:
            if position.quantity > 0:
                clients_by_isin[position.isin].add(position.client_id)

        report = []
        for isin, holders in sorted(clients_by_isin.items()):
            clients = sorted(holders)
            client_percentage = (Decimal(len(clients)) / total_clients * PERCENT).quantize(
                Decimal("0.01")
            )
            if client_percentage > CONCENTRATION_THRESHOLD:
                report.append(
                    {
                        "isin": isin,
                        "client_count": len(clients),
                        "client_percentage": client_percentage,
                        "clients": clients,
                    }
                )

        return report

    def _holding_time_result(
        self,
        client_id: str,
        weighted_seconds: Decimal,
        closed_quantity: Decimal,
    ) -> ReportRow:
        average_seconds = ZERO if closed_quantity == 0 else weighted_seconds / closed_quantity
        return {
            "client_id": client_id,
            "average_holding_seconds": average_seconds,
            "average_holding_days": (average_seconds / SECONDS_PER_DAY).quantize(Decimal("0.01")),
            "closed_quantity": closed_quantity,
        }

    def _portfolio_values_after_each_transaction(
        self,
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
