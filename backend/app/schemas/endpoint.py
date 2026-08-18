from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class EndpointResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    endpoint_identifier: str
    endpoint_name: str
    last_seen: datetime

