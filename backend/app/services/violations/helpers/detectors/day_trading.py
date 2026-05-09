from collections import defaultdict, deque
from datetime import timedelta

from backend.app.services.violations.schemas import (
    ClientContext,
    TransactionView,
    ViolationDraft,
    ViolationRule,
    ViolationSeverity,
    ViolationType,
)


class DayTradingRule(ViolationRule):
    def evaluate(self, ctx: ClientContext) -> list[ViolationDraft]:
        pair_threshold = 3
        transactions_by_isin: dict[str, list[TransactionView]] = defaultdict(list)
        for transaction in ctx.transactions:
            transactions_by_isin[transaction.isin].append(transaction)

        drafts: list[ViolationDraft] = []
        for isin, transactions in transactions_by_isin.items():
            max_pairs = _max_pairs_in_window(transactions)
            if max_pairs >= pair_threshold:
                drafts.append(
                    ViolationDraft(
                        client_id=ctx.client_id,
                        transaction_id=transactions[-1].transaction_id,
                        violation_type=ViolationType.DAY_TRADING,
                        severity=ViolationSeverity.WARNING,
                        message=(
                            f"{max_pairs} buy/sell pairs of {isin} within 24h "
                            f"(threshold: {pair_threshold})."
                        ),
                    )
                )
        return drafts


def detect_day_trading(ctx: ClientContext) -> list[ViolationDraft]:
    return DayTradingRule().evaluate(ctx)


def _max_pairs_in_window(transactions: list[TransactionView]) -> int:
    window: deque[TransactionView] = deque()
    buys = sells = max_pairs = 0
    period = timedelta(hours=24)

    for transaction in transactions:
        while window and transaction.timestamp - window[0].timestamp > period:
            expired = window.popleft()
            if expired.action == "buy":
                buys -= 1
            else:
                sells -= 1

        window.append(transaction)
        if transaction.action == "buy":
            buys += 1
        else:
            sells += 1

        max_pairs = max(max_pairs, min(buys, sells))

    return max_pairs
