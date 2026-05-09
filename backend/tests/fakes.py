from typing import Any


class FakeScalarResult:
    def __init__(self, rows: list[Any]) -> None:
        self.rows = rows

    def all(self) -> list[Any]:
        return self.rows


class FakeUploadSession:
    def __init__(self) -> None:
        self.added: list[Any] = []
        self.committed = False
        self.rolled_back = False

    def add_all(self, items: list[Any]) -> None:
        self.added.extend(items)

    def execute(self, _statement: Any) -> None:
        return None

    def flush(self) -> None:
        return None

    def scalars(self, _statement: Any) -> FakeScalarResult:
        transactions = [
            item for item in self.added if item.__class__.__name__ == "Transaction"
        ]
        return FakeScalarResult(transactions)

    def commit(self) -> None:
        self.committed = True

    def rollback(self) -> None:
        self.rolled_back = True


class FakePositionService:
    def __init__(self, positions: list[dict[str, Any]] | None = None) -> None:
        self.positions = positions or []
        self.refreshed = False

    def refresh_clients_positions(
        self,
        _client_ids: list[str],
        _transactions: list[Any],
    ) -> list[dict[str, Any]]:
        self.refreshed = True
        return self.positions
