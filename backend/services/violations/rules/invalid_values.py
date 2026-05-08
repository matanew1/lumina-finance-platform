from __future__ import annotations

from backend.services.violations.types import (
    ClientContext,
    ViolationDraft,
    ViolationSeverity,
    ViolationType,
)


class InvalidValuesRule:
    def detect(self, ctx: ClientContext) -> list[ViolationDraft]:
        drafts: list[ViolationDraft] = []
        for transaction in ctx.transactions:
            offenders = [] # List of fields with invalid values for this transaction
            if transaction.quantity < 0:
                offenders.append(f"quantity={transaction.quantity}")
            if transaction.price < 0:
                offenders.append(f"price={transaction.price}")
            if not offenders:
                continue
            drafts.append(
                ViolationDraft(
                    client_id=ctx.client_id,
                    transaction_id=transaction.transaction_id,
                    violation_type=ViolationType.INVALID_VALUES,
                    severity=ViolationSeverity.ERROR,
                    message=f"Negative value(s): {', '.join(offenders)}.",
                )
            )
        return drafts
