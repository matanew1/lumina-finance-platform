from backend.app.services.violations.schemas import (
    ClientContext,
    ViolationDraft,
    ViolationRule,
    ViolationSeverity,
    ViolationType,
)


class InvalidValuesRule(ViolationRule):
    def evaluate(self, ctx: ClientContext) -> list[ViolationDraft]:
        drafts: list[ViolationDraft] = []
        for transaction in ctx.transactions:
            offenders: list[str] = []
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


def detect_invalid_values(ctx: ClientContext) -> list[ViolationDraft]:
    return InvalidValuesRule().evaluate(ctx)
