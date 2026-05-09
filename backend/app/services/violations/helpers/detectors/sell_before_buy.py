from collections import defaultdict
from decimal import Decimal

from backend.app.schemas.violations import (
    ClientContext,
    ViolationDraft,
    ViolationSeverity,
    ViolationType,
)
from backend.app.utils.sorters import sort_by_timestamp


def detect_sell_before_buy(ctx: ClientContext) -> list[ViolationDraft]:
    """Sell Before Buy -> Flag as ERROR"""
    
    # For each ISIN, keep track of the running quantity of shares held by the client.
    running: dict[str, Decimal] = defaultdict(Decimal)
    drafts: list[ViolationDraft] = []

    transactions = sorted(ctx.transactions, key=sort_by_timestamp)
    
    for transaction in transactions:
        # if the transaction is a buy, add the quantity to the running total for that ISIN
        if transaction.action == "buy":
            running[transaction.isin] += transaction.quantity
        # if the transaction is a sell, check if the client has enough shares of that ISIN to sell
        elif transaction.action == "sell":
            # If the sell quantity is greater than the running total for that ISIN, add a violation
            if transaction.quantity > running[transaction.isin]:
                drafts.append(ViolationDraft(
                    client_id=ctx.client_id,
                    transaction_id=transaction.transaction_id,
                    violation_type=ViolationType.SELL_BEFORE_BUY,
                    severity=ViolationSeverity.ERROR,
                    message=(
                        f"Sell of {transaction.quantity} {transaction.isin} "
                        f"exceeds available position ({running[transaction.isin]})."
                    ),
                ))
            # Subtract the sell quantity from the running total for that ISIN
            running[transaction.isin] -= transaction.quantity

    return drafts
