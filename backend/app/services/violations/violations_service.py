from collections import defaultdict
from collections.abc import Iterable
from typing import Protocol

from backend.app.schemas.positions import PositionSnapshot, PositionView
from backend.app.schemas.violations import (
    ClientContext,
    TransactionView,
    ViolationDraft,
    ViolationResponse,
    ViolationRule,
    ViolationType,
)
from backend.app.services.positions.helpers.snapshots import position_snapshot_from
from backend.app.services.violations.helpers.detectors import (
    detect_day_trading,
    detect_invalid_values,
    detect_risk_concentration,
    detect_sell_before_buy,
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


class ViolationRepositoryProtocol(Protocol):
    def list_violations(self, client_id: str | None = None) -> list: ...


def detect_violations(
    transactions: Iterable[TransactionView],
    positions: Iterable[PositionView],
    rules: Iterable[ViolationRule] = DEFAULT_RULES,
) -> list[ViolationDraft]:
    """Run each rule against every client's transactions and positions."""
    transactions_by_client: dict[str, list[TransactionView]] = defaultdict(list)
    positions_by_client: dict[str, list[PositionSnapshot]] = defaultdict(list)

    for t in transactions:
        transactions_by_client[t.client_id].append(t)
    for p in positions:
        snap = position_snapshot_from(p)
        positions_by_client[snap.client_id].append(snap)

    drafts: list[ViolationDraft] = []
    client_ids = sorted(set(transactions_by_client) | set(positions_by_client))

    for client_id in client_ids:
        ctx = ClientContext(
            client_id=client_id,
            transactions=sorted(
                transactions_by_client[client_id],
                key=sort_by_timestamp_and_id,
            ),
            positions=positions_by_client[client_id],
        )
        for rule in rules:
            drafts.extend(rule(ctx))

    return drafts


def list_violations(
    repository: ViolationRepositoryProtocol,
    client_id: str | None = None,
) -> list[ViolationResponse]:
    return [
        ViolationResponse.model_validate(v)
        for v in repository.list_violations(client_id=client_id)
    ]


def validate_transactions_can_build_positions(
    transactions: list[TransactionView],
) -> None:
    """Raise if any blocking rule fires; surfaces *all* blocking messages."""
    drafts = detect_violations(transactions, [], BLOCKING_RULES)
    if not drafts:
        return

    messages = "; ".join(d.message for d in drafts)
    if any(d.violation_type == ViolationType.SELL_BEFORE_BUY for d in drafts):
        raise InsufficientQuantityError(messages)
    raise ValidationAppError(messages)
