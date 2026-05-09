from collections import Counter

from backend.app.schemas.analytics import TopTradedIsin, TransactionView
from backend.app.utils.constants import TOP_TRADED_LIMIT


def calculate_top_traded_isins(
    transactions: list[TransactionView],
    limit: int = TOP_TRADED_LIMIT,
) -> list[TopTradedIsin]:
    '''
    Calculate the top traded ISINs from a list of transactions.
    
    - Parameters:
        - transactions: list[TransactionView] - The transactions to process.
        - limit: int - The maximum number of top traded ISINs to return.
    - Returns:
        - list[TopTradedIsin] - The top traded ISINs.
    '''
    # Count the number of times each ISIN appears in the transactions
    counts = Counter(sorted(transaction.isin for transaction in transactions))
    # Return the top N most common ISINs
    return [
        TopTradedIsin(isin=isin, transaction_count=transaction_count)
        for isin, transaction_count in counts.most_common(limit)
    ]
