from collections.abc import Iterable

from backend.app.schemas.positions import (
    PositionSnapshot,
    PositionView,
    TransactionView,
)


def build_position_snapshots(
    transactions: list[TransactionView],
    positions: Iterable[PositionView],
) -> list[PositionSnapshot]:
    """
    Builds position snapshots for the given transactions and positions.
    
    - Parameters:
        - transactions: list[TransactionView] - The transactions to process.
        - positions: Iterable[PositionView] - The positions to process.
    - Returns:
        - list[PositionSnapshot] - The position snapshots.
    """
    latest_transaction_ids = {
        (transaction.client_id, transaction.isin): transaction.transaction_id
        for transaction in transactions
    }
    return [
        PositionSnapshot(
            client_id=position.client_id,
            isin=position.isin,
            quantity=position.quantity,
            market_price=position.market_price,
            transaction_id=latest_transaction_ids.get((position.client_id, position.isin)),
        )
        for position in positions
        if position.quantity > 0
    ]


def position_snapshot_from(position: PositionView) -> PositionSnapshot:
    """
    Creates a position snapshot from a position view.
    
    - Parameters:
        - position: PositionView - The position view to convert.
    - Returns:
        - PositionSnapshot - The position snapshot.
    """
    return PositionSnapshot(
        client_id=position.client_id,
        isin=position.isin,
        quantity=position.quantity,
        market_price=position.market_price,
        transaction_id=getattr(position, "transaction_id", None),
    )
