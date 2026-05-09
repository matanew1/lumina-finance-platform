from decimal import Decimal

from backend.app.services.shared.decimal_utils import ZERO, percentage
from backend.app.services.violations.schemas import (
    ClientContext,
    ViolationDraft,
    ViolationRule,
    ViolationSeverity,
    ViolationType,
)


class RiskConcentrationRule(ViolationRule):
    def evaluate(self, ctx: ClientContext) -> list[ViolationDraft]:
        if not ctx.positions:
            return []

        threshold = Decimal("0.5")
        market_values = [
            (position, position.quantity * position.market_price)
            for position in ctx.positions
        ]
        total_market_value = sum((value for _, value in market_values), ZERO)
        if total_market_value <= 0:
            return []

        drafts: list[ViolationDraft] = []
        for position, value in market_values:
            if value > threshold * total_market_value:
                share_pct = percentage(value, total_market_value)
                drafts.append(
                    ViolationDraft(
                        client_id=ctx.client_id,
                        transaction_id=position.transaction_id,
                        violation_type=ViolationType.RISK_CONCENTRATION,
                        severity=ViolationSeverity.WARNING,
                        message=(
                            f"{position.isin} is {share_pct}% of portfolio "
                            "(threshold: 50%)."
                        ),
                    )
                )
        return drafts


def detect_risk_concentration(ctx: ClientContext) -> list[ViolationDraft]:
    return RiskConcentrationRule().evaluate(ctx)
