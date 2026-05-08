from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal

from backend.services.violations import (
    PositionSnapshot,
    ViolationSeverity,
    ViolationType,
    build_default_engine,
)
from backend.services.violations.engine import ViolationEngine
from backend.services.violations.rules import (
    DayTradingRule,
    InvalidValuesRule,
    RiskConcentrationRule,
    SellBeforeBuyRule,
)
from backend.services.violations.types import ClientContext


@dataclass
class TxStub:
    client_id: str
    transaction_id: str
    isin: str
    action: str
    quantity: Decimal
    price: Decimal
    timestamp: datetime
    id: int = 1


def tx(
    transaction_id: str,
    action: str,
    quantity: str,
    price: str,
    *,
    isin: str = "US1234567890",
    client_id: str = "C001",
    minutes_offset: int = 0,
    base_time: datetime = datetime(2024, 1, 1, 9, 0, 0),
) -> TxStub:
    return TxStub(
        client_id=client_id,
        transaction_id=transaction_id,
        isin=isin,
        action=action,
        quantity=Decimal(quantity),
        price=Decimal(price),
        timestamp=base_time + timedelta(minutes=minutes_offset),
    )


def test_invalid_values_rule_flags_negative_quantity_and_price() -> None:
    rule = InvalidValuesRule()
    ctx = ClientContext(
        client_id="C001",
        transactions=[
            tx("T1", "buy", "10", "100"),
            tx("T2", "buy", "-5", "100"),
            tx("T3", "buy", "5", "-100"),
            tx("T4", "buy", "-1", "-1"),
        ],
    )

    drafts = rule.detect(ctx)
    transaction_ids = {draft.transaction_id for draft in drafts}

    assert {draft.violation_type for draft in drafts} == {ViolationType.INVALID_VALUES}
    assert {draft.severity for draft in drafts} == {ViolationSeverity.ERROR}
    assert transaction_ids == {"T2", "T3", "T4"}


def test_sell_before_buy_rule_flags_sell_with_no_prior_buy() -> None:
    rule = SellBeforeBuyRule()
    ctx = ClientContext(
        client_id="C001",
        transactions=[
            tx("T1", "sell", "10", "100", minutes_offset=0),
            tx("T2", "buy", "5", "100", minutes_offset=10),
            tx("T3", "sell", "10", "100", minutes_offset=20),
        ],
    )

    drafts = rule.detect(ctx)

    assert {draft.transaction_id for draft in drafts} == {"T1", "T3"}
    for draft in drafts:
        assert draft.violation_type == ViolationType.SELL_BEFORE_BUY
        assert draft.severity == ViolationSeverity.ERROR


def test_sell_before_buy_rule_does_not_flag_when_quantity_available() -> None:
    rule = SellBeforeBuyRule()
    ctx = ClientContext(
        client_id="C001",
        transactions=[
            tx("T1", "buy", "10", "100", minutes_offset=0),
            tx("T2", "sell", "5", "120", minutes_offset=10),
            tx("T3", "sell", "5", "130", minutes_offset=20),
        ],
    )

    assert rule.detect(ctx) == []


def test_day_trading_rule_flags_when_more_than_three_pairs_in_24h() -> None:
    rule = DayTradingRule()
    transactions = []
    for i in range(4):
        transactions.append(tx(f"B{i}", "buy", "1", "100", minutes_offset=i * 10))
        transactions.append(tx(f"S{i}", "sell", "1", "100", minutes_offset=i * 10 + 5))

    drafts = rule.detect(ClientContext(client_id="C001", transactions=transactions))

    assert len(drafts) == 1
    assert drafts[0].violation_type == ViolationType.DAY_TRADING
    assert drafts[0].severity == ViolationSeverity.WARNING
    assert "US1234567890" in drafts[0].message


def test_day_trading_rule_does_not_flag_three_pairs_or_fewer() -> None:
    rule = DayTradingRule()
    transactions = []
    for i in range(3):
        transactions.append(tx(f"B{i}", "buy", "1", "100", minutes_offset=i * 10))
        transactions.append(tx(f"S{i}", "sell", "1", "100", minutes_offset=i * 10 + 5))

    drafts = rule.detect(ClientContext(client_id="C001", transactions=transactions))

    assert drafts == []


def test_day_trading_rule_uses_24h_sliding_window() -> None:
    rule = DayTradingRule()
    transactions = []
    for i in range(4):
        transactions.append(tx(f"B{i}", "buy", "1", "100", minutes_offset=i * 60 * 24))
        transactions.append(tx(f"S{i}", "sell", "1", "100", minutes_offset=i * 60 * 24 + 60))

    drafts = rule.detect(ClientContext(client_id="C001", transactions=transactions))

    assert drafts == []


def test_risk_concentration_rule_flags_position_above_50_percent() -> None:
    rule = RiskConcentrationRule()
    ctx = ClientContext(
        client_id="C001",
        positions=[
            PositionSnapshot(
                client_id="C001",
                isin="ISIN_A",
                quantity=Decimal("10"),
                market_price=Decimal("70"),
                transaction_id="T_ISIN_A",
            ),
            PositionSnapshot(
                client_id="C001",
                isin="ISIN_B",
                quantity=Decimal("10"),
                market_price=Decimal("30"),
                transaction_id="T_ISIN_B",
            ),
        ],
    )

    drafts = rule.detect(ctx)

    assert len(drafts) == 1
    assert drafts[0].violation_type == ViolationType.RISK_CONCENTRATION
    assert drafts[0].severity == ViolationSeverity.WARNING
    assert drafts[0].transaction_id == "T_ISIN_A"
    assert "ISIN_A" in drafts[0].message


def test_risk_concentration_rule_does_not_flag_balanced_portfolio() -> None:
    rule = RiskConcentrationRule()
    ctx = ClientContext(
        client_id="C001",
        positions=[
            PositionSnapshot(client_id="C001", isin="ISIN_A", quantity=Decimal("10"), market_price=Decimal("50")),
            PositionSnapshot(client_id="C001", isin="ISIN_B", quantity=Decimal("10"), market_price=Decimal("50")),
        ],
    )

    assert rule.detect(ctx) == []


def test_engine_groups_transactions_by_client_and_runs_all_rules() -> None:
    engine = build_default_engine()
    transactions = [
        tx("T1", "buy", "10", "100", client_id="C001", minutes_offset=0),
        tx("T2", "sell", "5", "120", client_id="C001", minutes_offset=10),
        tx("T3", "buy", "1", "10", client_id="C002", minutes_offset=0),
    ]
    positions = [
        PositionSnapshot(client_id="C001", isin="US1234567890", quantity=Decimal("5"), market_price=Decimal("120")),
        PositionSnapshot(client_id="C002", isin="US1234567890", quantity=Decimal("1"), market_price=Decimal("10")),
    ]

    drafts = engine.run(transactions, positions)
    by_client = {draft.client_id for draft in drafts}

    assert by_client.issubset({"C001", "C002"})
    for draft in drafts:
        assert draft.violation_type in {
            ViolationType.DAY_TRADING,
            ViolationType.RISK_CONCENTRATION,
            ViolationType.SELL_BEFORE_BUY,
            ViolationType.INVALID_VALUES,
        }


def test_engine_invocation_with_no_data_returns_empty_list() -> None:
    engine = ViolationEngine([DayTradingRule(), RiskConcentrationRule()])
    assert engine.run([], []) == []
