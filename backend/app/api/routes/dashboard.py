from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.routes.analyses import to_list_item
from app.database.session import get_db
from app.repositories.analysis_repository import AnalysisRepository


router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/summary")
def dashboard_summary(db: Session = Depends(get_db)) -> dict:
    summary = AnalysisRepository(db).dashboard_summary()
    summary["recent"] = [to_list_item(item).model_dump() for item in summary["recent"]]
    summary["recent_threats"] = [
        to_list_item(item).model_dump() for item in summary["recent_threats"]
    ]
    return summary

