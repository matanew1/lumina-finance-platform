from collections import defaultdict
from collections.abc import Iterable

from backend.app.api.schemas.violations import ViolationResponse
from backend.app.services.positions.helpers.snapshots import position_snapshot_from
from backend.app.services.positions.schemas import PositionSnapshot, PositionView
from backend.app.services.violations.helpers.detectors import (
    DayTradingRule,
    InvalidValuesRule,
    RiskConcentrationRule,
    SellBeforeBuyRule,
)
from backend.app.services.violations.schemas import (
    ClientContext,
    TransactionView,
    ViolationDraft,
    ViolationRule,
    ViolationType,
)
from backend.app.utils.exceptions import InsufficientQuantityError

DEFAULT_RULES: tuple[ViolationRule, ...] = (
    InvalidValuesRule(),
    SellBeforeBuyRule(),
    DayTradingRule(),
    RiskConcentrationRule(),
)
BLOCKING_RULES = (SellBeforeBuyRule(),)


def detect_violations(
    transactions: Iterable[TransactionView],
    positions: Iterable[PositionView],
    rules: Iterable[ViolationRule] = DEFAULT_RULES,
) -> list[ViolationDraft]:
    transactions_by_client: dict[str, list[TransactionView]] = defaultdict(list)
    positions_by_client: dict[str, list[PositionSnapshot]] = defaultdict(list)

    for transaction in transactions:
        transactions_by_client[transaction.client_id].append(transaction)
    for position in positions:
        position_snapshot = position_snapshot_from(position)
        positions_by_client[position_snapshot.client_id].append(position_snapshot)

    drafts: list[ViolationDraft] = []
    for client_id in sorted(set(transactions_by_client) | set(positions_by_client)):
        ctx = ClientContext(
            client_id=client_id,
            transactions=sorted(
                transactions_by_client[client_id],
                key=lambda transaction: (
                    transaction.timestamp,
                    getattr(transaction, "id", 0),
                ),
            ),
            positions=positions_by_client[client_id],
        )
        for rule in rules:
            drafts.extend(rule(ctx))

    return drafts


def list_violations(
    repository,
    client_id: str | None = None,
) -> list[ViolationResponse]:
    return [
        ViolationResponse.model_validate(violation)
        for violation in repository.list_violations(client_id=client_id)
    ]


def validate_transactions_can_build_positions(
    transactions: list[TransactionView],
) -> None:
    drafts = detect_violations(transactions, [], BLOCKING_RULES)
    blocking_draft = next(
        (
            draft
            for draft in drafts
            if draft.violation_type == ViolationType.SELL_BEFORE_BUY
        ),
        None,
    )
    if blocking_draft is not None:
        raise InsufficientQuantityError(blocking_draft.message)
