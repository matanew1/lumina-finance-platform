from typing import Any, Protocol


class AnalyticsCalculator(Protocol):
    report_name: str

    def calculate(self, transactions: list[Any], positions: list[Any]) -> object:
        """Return one named analytics report from processed data."""
