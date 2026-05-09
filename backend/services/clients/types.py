from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ClientResponse:
    client_id: str

    def as_dict(self) -> dict[str, str]:
        return {"client_id": self.client_id}
