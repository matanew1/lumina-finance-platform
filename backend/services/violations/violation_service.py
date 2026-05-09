from collections import defaultdict
from collections.abc import Iterable
from typing import Any, Optional

from backend.db.repositories.violations.repository import ViolationRepository
from backend.services.violations.rules.day_trading import DayTradingRule
from backend.services.violations.rules.invalid_values import InvalidValuesRule
from backend.services.violations.rules.risk_concentration import RiskConcentrationRule
from backend.services.violations.rules.sell_before_buy import SellBeforeBuyRule
from backend.services.violations.types import (
    ClientContext,
    PositionSnapshot,
    PositionView,
    TransactionView,
    ViolationDraft,
    ViolationType,
)
from backend.utils.errors.exceptions import BadRequestError


class ViolationService:
    def __init__(
        self,
        violation_repository: ViolationRepository,
        rules: Iterable[Any] | None = None,
        blocking_rules: Iterable[Any] | None = None,
    ) -> None:
        self.violation_repository = violation_repository
        self.rules = list(rules or self._default_rules())
        self.blocking_rules = list(blocking_rules or (SellBeforeBuyRule(),))

    def list_violations(self, client_id: Optional[str] = None) -> list:
        return self.violation_repository.list_violations(client_id=client_id)

    def detect_violations(
        self,
        transactions: Iterable[TransactionView],
        positions: Iterable[PositionView],
    ) -> list[ViolationDraft]:
        return self._detect_with_rules(transactions, positions, self.rules)

    def validate_transactions_can_build_positions(self, transactions: list[Any]) -> None:
        drafts = self._detect_with_rules(transactions, [], self.blocking_rules)
        blocking_draft = next(
            (
                draft
                for draft in drafts
                if draft.violation_type == ViolationType.SELL_BEFORE_BUY
            ),
            None,
        )
        if blocking_draft is not None:
            raise BadRequestError(blocking_draft.message)

    def refresh_clients_violations(
        self,
        client_ids: Iterable[str],
        transactions: list[Any],
        positions: list[dict[str, Any]],
    ) -> None:
        position_snapshots = self._build_position_snapshots(transactions, positions)
        drafts = self.detect_violations(transactions, position_snapshots)
        self.violation_repository.update_clients_violations(client_ids, drafts)

    @staticmethod
    def _default_rules() -> tuple[Any, ...]:
        return (
            InvalidValuesRule(),
            SellBeforeBuyRule(),
            DayTradingRule(),
            RiskConcentrationRule(),
        )

    @staticmethod
    def _detect_with_rules(
        transactions: Iterable[TransactionView],
        positions: Iterable[PositionView],
        rules: Iterable[Any],
    ) -> list[ViolationDraft]:
        transactions_by_client: dict[str, list[TransactionView]] = defaultdict(list)
        positions_by_client: dict[str, list[PositionSnapshot]] = defaultdict(list)

        for transaction in transactions:
            transactions_by_client[transaction.client_id].append(transaction)
        for position in positions:
            position_snapshot = ViolationService._position_snapshot_from(position)
            positions_by_client[position_snapshot.client_id].append(position_snapshot)

        drafts: list[ViolationDraft] = []
        for client_id in sorted(set(transactions_by_client) | set(positions_by_client)):
            ctx = ClientContext(
                client_id=client_id,
                transactions=sorted(
                    transactions_by_client[client_id],
                    key=lambda transaction: (transaction.timestamp, getattr(transaction, "id", 0)),
                ),
                positions=positions_by_client[client_id],
            )
            for rule in rules:
                drafts.extend(rule.detect(ctx))

        return drafts

    @staticmethod
    def _build_position_snapshots(
        transactions: list[Any],
        positions: list[dict[str, Any]],
    ) -> list[PositionSnapshot]:
        latest_transaction_ids = {
            (transaction.client_id, transaction.isin): transaction.transaction_id
            for transaction in transactions
        }
        return [
            PositionSnapshot(
                client_id=position["client_id"],
                isin=position["isin"],
                quantity=position["quantity"],
                market_price=position["market_price"],
                transaction_id=latest_transaction_ids.get(
                    (position["client_id"], position["isin"])
                ),
            )
            for position in positions
            if position["quantity"] > 0
        ]

    @staticmethod
    def _position_snapshot_from(position: PositionView) -> PositionSnapshot:
        if isinstance(position, dict):
            return PositionSnapshot(
                client_id=position["client_id"],
                isin=position["isin"],
                quantity=position["quantity"],
                market_price=position["market_price"],
                transaction_id=position.get("transaction_id"),
            )

        return PositionSnapshot(
            client_id=position.client_id,
            isin=position.isin,
            quantity=position.quantity,
            market_price=position.market_price,
            transaction_id=position.transaction_id,
        )
