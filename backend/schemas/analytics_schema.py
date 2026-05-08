from typing import Any

from pydantic import Field

from backend.schemas.common import OrmSchema


class AnalyticsRead(OrmSchema):
    summary: dict[str, Any] = Field(default_factory=dict)

    # TODO: replace placeholder summary with explicit analytics fields.
