from datetime import timedelta
from decimal import Decimal

# Decimal Defaults
ZERO = Decimal("0")
CENT = Decimal("0.01")
PERCENT = Decimal("100")
# Matches the Numeric(18, 6) scale used by the positions table; quantizing
# Decimal results to this scale at output boundaries keeps API responses
# stable and prevents repeating-decimal drift from divisions.
MONEY_QUANTUM = Decimal("0.000001")

# Analytics Thresholds
SECONDS_PER_DAY = Decimal("86400")
ANALYTICS_CONCENTRATION_THRESHOLD = Decimal("70.00")
TOP_TRADED_LIMIT = 3

# Violations Thresholds
DAY_TRADING_PAIR_THRESHOLD = 3
DAY_TRADING_WINDOW = timedelta(hours=24)
RISK_CONCENTRATION_THRESHOLD = Decimal("0.5")

# Transaction Ingestion
REQUIRED_COLUMNS = (
    "client_id",
    "transaction_id",
    "isin",
    "action",
    "quantity",
    "price",
    "timestamp",
)
COLUMN_ALIASES = {
    "clientid": "client_id",
    "transactionid": "transaction_id",
    "isin": "isin",
    "action": "action",
    "quantity": "quantity",
    "price": "price",
    "timestamp": "timestamp",
}
STRING_COLUMNS = ("client_id", "transaction_id", "isin", "action")
VALID_ACTIONS = {"buy", "sell"}
