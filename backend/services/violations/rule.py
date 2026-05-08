from __future__ import annotations

from typing import Protocol

from backend.services.violations.types import ClientContext, ViolationDraft


class ViolationRule(Protocol):
    def detect(self, ctx: ClientContext) -> list[ViolationDraft]: ...
