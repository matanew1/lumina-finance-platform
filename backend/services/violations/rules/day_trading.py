from __future__ import annotations

from collections import defaultdict, deque
from datetime import timedelta

from backend.services.violations.types import (
    ClientContext,
    ViolationDraft,
    ViolationSeverity,
    ViolationType,
)


class DayTradingRule:
    PAIR_THRESHOLD = 3
    WINDOW = timedelta(hours=24)

    def detect(self, ctx: ClientContext) -> list[ViolationDraft]:
        transactions_by_isin: dict[str, list] = defaultdict(list)
        for transaction in ctx.transactions:
            transactions_by_isin[transaction.isin].append(transaction)

        drafts: list[ViolationDraft] = []
        for isin, transactions in transactions_by_isin.items():
            max_pairs = self._max_pairs_in_window(transactions)
            if max_pairs > self.PAIR_THRESHOLD:
                drafts.append(
                    ViolationDraft(
                        client_id=ctx.client_id,
                        transaction_id=transactions[-1].transaction_id,
                        violation_type=ViolationType.DAY_TRADING,
                        severity=ViolationSeverity.WARNING,
                        message=f"{max_pairs} buy/sell pairs of {isin} within 24h (limit: {self.PAIR_THRESHOLD}).",
                    )
                )
        return drafts

    def _max_pairs_in_window(self, transactions: list) -> int:
        window: deque = deque()
        buys = sells = max_pairs = 0

        for transaction in transactions:

            # Remove expired transactions from the window 
            while window and transaction.timestamp - window[0].timestamp > self.WINDOW:
                expired = window.popleft()
                if expired.action == "buy":
                    buys -= 1
                else:
                    sells -= 1

            # Add the current transaction to the window
            window.append(transaction)
            if transaction.action == "buy":
                buys += 1
            else:
                sells += 1

            # Update the maximum number of pairs in the current window
            max_pairs = max(max_pairs, min(buys, sells))

        return max_pairs
