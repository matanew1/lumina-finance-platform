from backend.app.schemas.violations import (
    ClientContext,
    ViolationDraft,
    ViolationSeverity,
    ViolationType,
)


def detect_invalid_values(ctx: ClientContext) -> list[ViolationDraft]:
    """Price or Quantity < 0 -> flag as ERROR"""

    # Initialize a list to store violation drafts
    drafts: list[ViolationDraft] = []

    # Iterate over each transaction
    for t in ctx.transactions:
        # Check for negative quantity or price
        offenders = []
        if t.quantity < 0:
            offenders.append(f"quantity={t.quantity}")
        if t.price < 0:
            offenders.append(f"price={t.price}")

        # If there are offenders, add a violation draft
        if offenders:
            drafts.append(ViolationDraft(
                client_id=ctx.client_id,
                transaction_id=t.transaction_id,
                violation_type=ViolationType.INVALID_VALUES,
                severity=ViolationSeverity.ERROR,
                message=f"Negative value(s): {', '.join(offenders)}.",
            ))
    # Return the list of violation drafts
    return drafts
