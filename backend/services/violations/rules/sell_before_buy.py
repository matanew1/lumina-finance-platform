from __future__ import annotations

from collections import defaultdict
from decimal import Decimal

from backend.services.violations.types import (
    ClientContext,
    ViolationDraft,
    ViolationSeverity,
    ViolationType,
)


class SellBeforeBuyRule:
    def detect(self, ctx: ClientContext) -> list[ViolationDraft]:
        running: dict[str, Decimal] = defaultdict(lambda: Decimal("0"))
        drafts: list[ViolationDraft] = []

        for transaction in ctx.transactions:
            if transaction.action == "buy":
                running[transaction.isin] += transaction.quantity
            elif transaction.action == "sell":
                available = running[transaction.isin]
                if transaction.quantity > available:
                    drafts.append(
                        ViolationDraft(
                            client_id=ctx.client_id,
                            transaction_id=transaction.transaction_id,
                            violation_type=ViolationType.SELL_BEFORE_BUY,
                            severity=ViolationSeverity.ERROR,
                            message=(
                                f"Sell of {transaction.quantity} {transaction.isin} "
                                f"exceeds available position ({available})."
                            ),
                        )
                    )
                running[transaction.isin] = available - transaction.quantity

        return drafts
