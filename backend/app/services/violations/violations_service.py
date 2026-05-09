from collections import defaultdict
from collections.abc import Iterable

from backend.app.schemas.violations import ViolationResponse
from backend.app.services.positions.helpers.snapshots import position_snapshot_from
from backend.app.schemas.positions import PositionSnapshot, PositionView
from backend.app.services.violations.helpers.detectors import (
    detect_day_trading,
    detect_invalid_values,
    detect_risk_concentration,
    detect_sell_before_buy,
)
from backend.app.schemas.violations import (
    ClientContext,
    TransactionView,
    ViolationDraft,
    ViolationRule,
    ViolationType,
)
from backend.app.utils.exceptions import InsufficientQuantityError, ValidationAppError
from backend.app.utils.sorters import sort_by_timestamp_and_id

# Rules run on every ingestion batch, in order.
DEFAULT_RULES: tuple[ViolationRule, ...] = (
    detect_invalid_values,
    detect_sell_before_buy,
    detect_day_trading,
    detect_risk_concentration,
)

# Rules that block position-building if triggered.
BLOCKING_RULES: tuple[ViolationRule, ...] = (
    detect_invalid_values,
    detect_sell_before_buy,
)

# Rules persisted after blocking validation has already passed.
PERSISTED_RULES: tuple[ViolationRule, ...] = tuple(
    rule for rule in DEFAULT_RULES if rule not in BLOCKING_RULES
)


def detect_violations(
    transactions: Iterable[TransactionView],
    positions: Iterable[PositionView],
    rules: Iterable[ViolationRule] = DEFAULT_RULES,
) -> list[ViolationDraft]:
    """
    Detects violations in transactions and positions.
        
    - Parameters:
        - transactions: Iterable[TransactionView] - The transactions to process.
        - positions: Iterable[PositionView] - The positions to process.
        - rules: Iterable[ViolationRule] - The rules to apply.
    - Returns:
        - list[ViolationDraft] - The detected violations.
    """

    # Group transactions and positions by client ID
    transactions_by_client: dict[str, list[TransactionView]] = defaultdict(list)
    positions_by_client: dict[str, list[PositionSnapshot]] = defaultdict(list)

    # Populate the grouped transactions and positions
    for t in transactions:
        transactions_by_client[t.client_id].append(t)
    for p in positions:
        snap = position_snapshot_from(p)
        positions_by_client[snap.client_id].append(snap)

    # Initialize a list to store violation drafts
    drafts: list[ViolationDraft] = []

    # Get all unique client IDs from both transactions and positions
    client_ids = sorted(set(transactions_by_client) | set(positions_by_client))

    # Iterate over each client ID
    for client_id in client_ids:
        # Create a client context with the client's transactions and positions
        ctx = ClientContext(
            client_id=client_id,
            transactions=sorted(
                transactions_by_client[client_id],
                key=sort_by_timestamp_and_id,
            ),
            positions=positions_by_client[client_id],
        )
        # Apply each rule to the client context and add any violations to the list
        for rule in rules:
            drafts.extend(rule(ctx))

    # Return the list of violation drafts
    return drafts


def list_violations(
    repository,
    client_id: str | None = None,
) -> list[ViolationResponse]:
    return [
        ViolationResponse.model_validate(v)
        for v in repository.list_violations(client_id=client_id)
    ]


def validate_transactions_can_build_positions(
    transactions: list[TransactionView],
) -> None:
    """
    Validates that transactions can be used to build positions.
    
    - Parameters:
        - transactions: list[TransactionView] - The transactions to process.
    - Returns:
        - None
    """
    # Run the blocking rules against the transactions
    drafts = detect_violations(transactions, [], BLOCKING_RULES)

    # Any draft from a blocking rule prevents position-building.
    blocking = next(iter(drafts), None)

    # If there is a blocking violation, raise an exception
    if blocking is not None:
        if blocking.violation_type == ViolationType.SELL_BEFORE_BUY:
            raise InsufficientQuantityError(blocking.message)
        raise ValidationAppError(blocking.message)
