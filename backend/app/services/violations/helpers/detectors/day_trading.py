from collections import defaultdict, deque
from datetime import timedelta

from backend.app.schemas.violations import (
    ClientContext,
    TransactionView,
    ViolationDraft,
    ViolationSeverity,
    ViolationType,
)
from backend.app.utils.constants import DAY_TRADING_PAIR_THRESHOLD, DAY_TRADING_WINDOW


def detect_day_trading(ctx: ClientContext) -> list[ViolationDraft]:
    """More than 3 buy/sell pairs within 24 hours -> flag as Day Trading"""
    # Group transactions by ISIN
    transactions_by_isin: dict[str, list[TransactionView]] = defaultdict(list)
    for t in ctx.transactions:
        transactions_by_isin[t.isin].append(t)

    # For each ISIN, check if it has any violations 
    return [
        ViolationDraft(
            client_id=ctx.client_id,
            transaction_id=txns[-1].transaction_id,
            violation_type=ViolationType.DAY_TRADING,
            severity=ViolationSeverity.WARNING,
            message=f"{pairs} buy/sell pairs of {isin} within 24h (threshold: >{DAY_TRADING_PAIR_THRESHOLD}).",
        )
        for isin, txns in transactions_by_isin.items()
        if (pairs := _max_pairs_in_window(txns)) > DAY_TRADING_PAIR_THRESHOLD
    ]


def _max_pairs_in_window(transactions: list[TransactionView]) -> int:
    """
    Sliding-window count of matched buy/sell pairs within 24 hours.

    Logic:
    - Two deques hold the timestamps of buys and sells currently inside the window.
    - When the oldest entry falls outside the 24-hour boundary it is popped.
    - A 'pair' is one buy + one sell — so min(len(buys), len(sells)) is the number of matched pairs at any point in time.
    """
    buys: deque = deque()   # timestamps of buys inside the window
    sells: deque = deque()  # timestamps of sells inside the window
    max_pairs = 0

    # Iterate over each transaction, sorted by timestamp
    for transaction in transactions:  # pre-sorted by timestamp in detect_violations
        # Window is half-open (cutoff, current]: a trade exactly DAY_TRADING_WINDOW
        # ago is *outside* the 24h lookback. Using `<=` here (not `<`) prevents an
        # off-by-one that would pair trades exactly 24h apart.
        cutoff = transaction.timestamp - DAY_TRADING_WINDOW

        while buys and buys[0] <= cutoff:
            buys.popleft()

        while sells and sells[0] <= cutoff:
            sells.popleft()

        # Add the current transaction to the appropriate deque
        if transaction.action == "buy":
            buys.append(transaction.timestamp)
        else:
            sells.append(transaction.timestamp) 
            
        # Update the maximum number of pairs
        max_pairs = max(max_pairs, min(len(buys), len(sells)))

    return max_pairs
