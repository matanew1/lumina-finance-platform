from __future__ import annotations

from decimal import Decimal

from backend.services.violations.types import (
    ClientContext,
    ViolationDraft,
    ViolationSeverity,
    ViolationType,
)


class RiskConcentrationRule:
    THRESHOLD = Decimal("0.5")

    def detect(self, ctx: ClientContext) -> list[ViolationDraft]:

        # If there are no positions, we can't say there's a risk concentration violation.
        if not ctx.positions:
            return []

        # Calculate the total market value of the portfolio
        market_values = [
            (position, position.quantity * position.market_price) for position in ctx.positions
        ]
        total_market_value = sum((value for _, value in market_values), Decimal("0"))

        # If the total market value is zero, we can't say there's a risk concentration violation
        if total_market_value <= 0:
            return []

        drafts: list[ViolationDraft] = []
        for position, value in market_values:
            if value > self.THRESHOLD * total_market_value:
                share_pct = (value / total_market_value * Decimal("100")).quantize(
                    Decimal("0.01")
                )
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
