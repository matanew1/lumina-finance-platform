from collections import defaultdict, deque
from decimal import Decimal

from backend.app.schemas.analytics import (
    ClientAverageHoldingTime,
    HoldingLot,
    HoldingTimeTotals,
    TransactionView,
)
from backend.app.utils.constants import CENT, SECONDS_PER_DAY, ZERO
from backend.app.utils.exceptions import ValidationAppError

_HoldingsByAsset = dict[tuple[str, str], deque[HoldingLot]]
_TotalsByClient = dict[str, HoldingTimeTotals]


def calculate_average_holding_time_per_client(
    transactions: list[TransactionView],
) -> list[ClientAverageHoldingTime]:
    """
    Calculate the average holding time per client from a list of transactions.
    
    Args:
        transactions (list[TransactionView]): A list of transactions to process.
    
    Returns:
        list[ClientAverageHoldingTime]: A list of ClientAverageHoldingTime objects.
    """
    
    # get all unique client ids and sort them
    client_ids = sorted({transaction.client_id for transaction in transactions})
    
    # initialize a dictionary to store the holdings by asset
    holdings_by_asset: _HoldingsByAsset = defaultdict(deque)
    # initialize a dictionary to store the totals by client
    totals_by_client: _TotalsByClient = defaultdict(HoldingTimeTotals)

    # process each transaction
    for transaction in transactions:
        holdings = holdings_by_asset[(transaction.client_id, transaction.isin)]

        if transaction.action == "buy":
            # apply buy transaction
            _apply_open_holding(transaction, holdings)
        elif transaction.action == "sell":
            # apply sell transaction
            _apply_close_holding(
                transaction,
                holdings,
                totals_by_client[transaction.client_id],
            )
        else:
            raise ValidationAppError(
                f"Unsupported transaction action: {transaction.action}."
            )

    # return the results for each client
    return [
        _holding_time_result(client_id, totals_by_client[client_id])
        for client_id in client_ids
    ]


def _apply_open_holding(
    transaction: TransactionView,
    holdings: deque[HoldingLot],
) -> None:
    """
    Apply a buy transaction to the holdings.
    
    Args:
        transaction (TransactionView): The buy transaction.
        holdings (deque[HoldingLot]): The open holdings.
    """

    holdings.append(
        HoldingLot(
            quantity=transaction.quantity,
            timestamp=transaction.timestamp,
        )
    )


def _apply_close_holding(
    transaction: TransactionView,
    holdings: deque[HoldingLot],
    holding_totals: HoldingTimeTotals,
) -> None:
    """
    Apply a sell transaction to the holdings.
    
    Args:
        transaction (TransactionView): The sell transaction.
        holdings (deque[HoldingLot]): The open holdings.
        holding_totals (HoldingTimeTotals): The totals.
    """
    
    # initialize remaining quantity to sell
    remaining = transaction.quantity

    # go through each lot
    while remaining > 0 and holdings:
        # get the oldest lot
        oldest_lot = holdings[0]
        # calculate the quantity to close
        closed_quantity = min(oldest_lot.quantity, remaining)
        # calculate the holding seconds
        holding_seconds = Decimal(
            str((transaction.timestamp - oldest_lot.timestamp).total_seconds())
        )
        # record the closed holding
        holding_totals.record_closed_holding(holding_seconds, closed_quantity)
        
        # update the oldest lot quantity and remaining quantity
        oldest_lot.quantity -= closed_quantity
        remaining -= closed_quantity

        # if the lot is empty, remove it
        if oldest_lot.quantity == 0:
            holdings.popleft()


def _holding_time_result(
    client_id: str,
    holding_totals: HoldingTimeTotals,
) -> ClientAverageHoldingTime:
    """
    Create a ClientAverageHoldingTime result from the given data.
    
    Args:
        client_id (str): The client ID.
        holding_totals (HoldingTimeTotals): The totals.
    """

    # get the average holding seconds
    average_seconds = _average_holding_seconds(holding_totals)
    # return the result
    return ClientAverageHoldingTime(
        client_id=client_id,
        average_holding_seconds=average_seconds,
        average_holding_days=(average_seconds / SECONDS_PER_DAY).quantize(CENT),
        closed_quantity=holding_totals.closed_quantity,
    )


def _average_holding_seconds(holding_totals: HoldingTimeTotals) -> Decimal:
    """
    Calculate the average holding seconds.
    
    Args:
        holding_totals (HoldingTimeTotals): The totals.
    """

    # if no closed holdings, return 0
    if holding_totals.closed_quantity == 0:
        return ZERO
    
    # return the average holding seconds (weighted average)
    # formula: sum(holding_seconds * quantity) / sum(quantity)
    return (holding_totals.quantity_weighted_holding_seconds / holding_totals.closed_quantity).quantize(CENT)
