from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.models import Endpoint


class EndpointRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def upsert(self, identifier: str, name: str) -> Endpoint:
        endpoint = self.db.scalar(
            select(Endpoint).where(Endpoint.endpoint_identifier == identifier)
        )
        if endpoint is None:
            endpoint = Endpoint(endpoint_identifier=identifier, endpoint_name=name)
        else:
            endpoint.endpoint_name = name
            endpoint.last_seen = datetime.now(timezone.utc)
        self.db.add(endpoint)
        self.db.commit()
        self.db.refresh(endpoint)
        return endpoint

    def list(self) -> list[Endpoint]:
        return list(self.db.scalars(select(Endpoint).order_by(Endpoint.last_seen.desc())).all())
