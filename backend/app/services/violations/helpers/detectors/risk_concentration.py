from decimal import Decimal

from backend.app.utils.decimal_utils import ZERO, percentage
from backend.app.schemas.violations import (
    ClientContext,
    ViolationDraft,
    ViolationSeverity,
    ViolationType,
)
from backend.app.utils.constants import RISK_CONCENTRATION_THRESHOLD


def detect_risk_concentration(ctx: ClientContext) -> list[ViolationDraft]:
    """One ISIN > 50% of portfolio -> flag as Potential Risk"""
    
    # If there are no positions, return an empty list
    if not ctx.positions:
        return []

    # Calculate the market value for each position and the total market value of all positions
    market_values = [(position, position.quantity * position.market_price) for position in ctx.positions]
    total_market_value = sum((market_value for _, market_value in market_values), ZERO)

    # If the total market value is zero or less, return an empty list
    if total_market_value <= 0:
        return []

    # Return a list of violation drafts for each position that exceeds the concentration threshold
    return [
        ViolationDraft(
            client_id=ctx.client_id,
            transaction_id=position.transaction_id,
            violation_type=ViolationType.RISK_CONCENTRATION,
            severity=ViolationSeverity.WARNING,
            message=f"{position.isin} is {percentage(market_value, total_market_value)}% of portfolio (threshold: 50%).",
        )
        for position, market_value in market_values
        if (market_value / total_market_value) > RISK_CONCENTRATION_THRESHOLD
    ]
