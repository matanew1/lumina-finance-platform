from decimal import Decimal

from backend.app.utils.constants import CENT, PERCENT, ZERO


def percentage(part: Decimal, whole: Decimal) -> Decimal:
    if whole == ZERO:
        return ZERO
    return (part / whole * PERCENT).quantize(CENT)
