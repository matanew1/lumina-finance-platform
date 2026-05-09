from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, TypeAlias


@dataclass(frozen=True)
class TransactionIngestionResult:
    records: list[dict[str, Any]] = field(default_factory=list)
    total_rows: int = 0
    valid_rows: int = 0
    invalid_rows: int = 0
    errors: list[dict[str, Any]] = field(default_factory=list)

    @property
    def has_errors(self) -> bool:
        return bool(self.errors)


TransactionRecord: TypeAlias = dict[str, Any]
TransactionUploadResponse: TypeAlias = dict[str, Any]
