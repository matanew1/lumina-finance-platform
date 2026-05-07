from pydantic import Field

from backend.schemas.common import OrmSchema


class ClientRead(OrmSchema):
    client_id: str = Field(examples=["C001"])

    # TODO: add client display name and metadata if a clients table is introduced.
