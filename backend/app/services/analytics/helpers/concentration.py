from collections import defaultdict
from decimal import Decimal

from backend.app.schemas.analytics import (
    IsinConcentrationEntry,
    PositionView,
    TransactionView,
)
from backend.app.utils.constants import ANALYTICS_CONCENTRATION_THRESHOLD
from backend.app.utils.decimal_utils import percentage


def calculate_isin_concentration_report(
    transactions: list[TransactionView],
    positions: list[PositionView],
) -> list[IsinConcentrationEntry]:
    """
    Calculate the ISIN concentration report.
    
    Args:
        transactions (list[TransactionView]): A list of transactions.
        positions (list[PositionView]): A list of positions.
    
    Returns:
        list[IsinConcentrationEntry]: A list of ISIN concentration entries.
    """

    # get the total number of clients
    total_clients = len({transaction.client_id for transaction in transactions})
    
    # if there are no clients, return an empty list
    if total_clients == 0:
        return []

    # initialize the report
    report: list[IsinConcentrationEntry] = []

    # filter out positions with zero quantity and get the clients by ISIN
    clients_by_isin: dict[str, set[str]] = defaultdict(set)
    for position in positions:
        if position.quantity > 0:
            clients_by_isin[position.isin].add(position.client_id)

    # sort the clients by ISIN
    sorted_clients = sorted(clients_by_isin.items())

    # get the concentration entries
    for isin, holders in sorted_clients:
        # create the concentration entry
        clients = sorted(holders)
        client_percentage = percentage(Decimal(len(clients)), Decimal(total_clients))
        # add the entry to the report if it meets the threshold
        if client_percentage > ANALYTICS_CONCENTRATION_THRESHOLD:
            report.append(
                IsinConcentrationEntry(
                    isin=isin,
                    client_count=len(clients),
                    client_percentage=client_percentage,
                    clients=clients,
                )
            )

    return report
