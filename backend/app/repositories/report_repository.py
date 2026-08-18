from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.models import Report


class ReportRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, **values) -> Report:
        report = Report(**values)
        self.db.add(report)
        self.db.commit()
        self.db.refresh(report)
        return report

    def save(self, report: Report) -> Report:
        self.db.add(report)
        self.db.commit()
        self.db.refresh(report)
        return report

    def get_for_analysis(self, analysis_id: int) -> Report | None:
        return self.db.scalar(select(Report).where(Report.analysis_id == analysis_id))

