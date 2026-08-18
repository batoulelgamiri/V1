from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.repositories.endpoint_repository import EndpointRepository
from app.schemas.endpoint import EndpointResponse


router = APIRouter(prefix="/endpoints", tags=["endpoints"])


@router.get("", response_model=list[EndpointResponse])
def list_endpoints(db: Session = Depends(get_db)) -> list[EndpointResponse]:
    return [EndpointResponse.model_validate(item) for item in EndpointRepository(db).list()]

