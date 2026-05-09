from decimal import Decimal

ZERO = Decimal("0")
CENT = Decimal("0.01")
PERCENT = Decimal("100")


def percentage(part: Decimal, whole: Decimal) -> Decimal:
    if whole == ZERO:
        return ZERO
    return (part / whole * PERCENT).quantize(CENT)
