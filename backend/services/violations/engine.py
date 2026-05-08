from __future__ import annotations

from collections import defaultdict
from typing import Iterable

from backend.services.violations.rule import ViolationRule
from backend.services.violations.rules import (
    DayTradingRule,
    InvalidValuesRule,
    RiskConcentrationRule,
    SellBeforeBuyRule,
)
from backend.services.violations.types import (
    ClientContext,
    PositionView,
    TransactionView,
    ViolationDraft,
)


class ViolationEngine:
    def __init__(self, rules: Iterable[ViolationRule]) -> None:
        self.rules: list[ViolationRule] = list(rules)

    def run(
        self,
        transactions: Iterable[TransactionView],
        positions: Iterable[PositionView],
    ) -> list[ViolationDraft]:
        transactions_by_client: dict[str, list[TransactionView]] = defaultdict(list) # Group transactions by client_id
        positions_by_client: dict[str, list[PositionView]] = defaultdict(list) # Group positions by client_id

        # Group transactions and positions by client_id for efficient access in rules
        for transaction in transactions:
            transactions_by_client[transaction.client_id].append(transaction)
        for position in positions:
            positions_by_client[position.client_id].append(position)

        # Get the set of all client_ids that have transactions or positions to evaluate
        client_ids = set(transactions_by_client) | set(positions_by_client)

        # Run each rule for each client context and collect violation drafts
        drafts: list[ViolationDraft] = []
        for client_id in sorted(client_ids):
            # Create a client context with the client's transactions and positions, sorted by timestamp
            ctx = ClientContext(
                client_id=client_id,
                transactions=sorted(
                    transactions_by_client[client_id],
                    key=lambda transaction: (transaction.timestamp, getattr(transaction, "id", 0)),
                ),
                positions=positions_by_client[client_id],
            )
            for rule in self.rules:
                drafts.extend(rule.detect(ctx)) # Run the rule's detection logic for this client context and collect any violation drafts it returns
        return drafts


def build_default_engine() -> ViolationEngine:
    return ViolationEngine(
        [
            InvalidValuesRule(),
            SellBeforeBuyRule(),
            DayTradingRule(),
            RiskConcentrationRule(),
        ]
    )
