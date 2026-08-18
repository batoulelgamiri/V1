from __future__ import annotations

from datetime import datetime, timedelta, timezone
from math import ceil

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.database.models import Analysis


class AnalysisRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, **values) -> Analysis:
        analysis = Analysis(**values)
        self.db.add(analysis)
        self.db.commit()
        self.db.refresh(analysis)
        return analysis

    def save(self, analysis: Analysis) -> Analysis:
        self.db.add(analysis)
        self.db.commit()
        self.db.refresh(analysis)
        return analysis

    def get(self, analysis_id: int) -> Analysis | None:
        statement = (
            select(Analysis)
            .options(selectinload(Analysis.report))
            .where(Analysis.id == analysis_id)
        )
        return self.db.scalar(statement)

    def find_cached(self, sha256: str, model_version: str) -> Analysis | None:
        statement = (
            select(Analysis)
            .options(selectinload(Analysis.report))
            .where(
                Analysis.sha256 == sha256,
                Analysis.model_version == model_version,
                Analysis.status == "completed",
                Analysis.classification.is_not(None),
            )
            .order_by(Analysis.cached_from_analysis_id.is_not(None), Analysis.created_at.asc())
            .limit(1)
        )
        return self.db.scalar(statement)

    def list(
        self,
        *,
        page: int,
        page_size: int,
        classification: str | None = None,
        source: str | None = None,
        search: str | None = None,
    ) -> tuple[list[Analysis], int, int]:
        filters = []
        if classification:
            filters.append(Analysis.classification == classification)
        if source:
            filters.append(Analysis.source == source)
        if search:
            term = f"%{search.strip()}%"
            filters.append(
                or_(
                    Analysis.original_filename.ilike(term),
                    Analysis.sha256.ilike(term),
                    Analysis.endpoint_name.ilike(term),
                    Analysis.file_path.ilike(term),
                )
            )

        total = self.db.scalar(select(func.count(Analysis.id)).where(*filters)) or 0
        statement = (
            select(Analysis)
            .options(selectinload(Analysis.report))
            .where(*filters)
            .order_by(Analysis.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        items = list(self.db.scalars(statement).all())
        return items, total, max(1, ceil(total / page_size))

    def dashboard_summary(self) -> dict:
        total = self.db.scalar(select(func.count(Analysis.id))) or 0
        counts = dict(
            self.db.execute(
                select(Analysis.classification, func.count(Analysis.id))
                .where(Analysis.classification.is_not(None))
                .group_by(Analysis.classification)
            ).all()
        )
        recent = list(
            self.db.scalars(
                select(Analysis)
                .options(selectinload(Analysis.report))
                .order_by(Analysis.created_at.desc())
                .limit(8)
            ).all()
        )
        threats = list(
            self.db.scalars(
                select(Analysis)
                .options(selectinload(Analysis.report))
                .where(Analysis.classification.in_(["suspicious", "malicious"]))
                .order_by(Analysis.created_at.desc())
                .limit(6)
            ).all()
        )

        start = datetime.now(timezone.utc).date() - timedelta(days=6)
        raw_activity = self.db.execute(
            select(func.date(Analysis.created_at), func.count(Analysis.id))
            .where(
                Analysis.created_at
                >= datetime.combine(start, datetime.min.time(), tzinfo=timezone.utc)
            )
            .group_by(func.date(Analysis.created_at))
        ).all()
        activity_by_day = {str(day): count for day, count in raw_activity}
        activity = [
            {
                "date": (start + timedelta(days=offset)).isoformat(),
                "count": activity_by_day.get((start + timedelta(days=offset)).isoformat(), 0),
            }
            for offset in range(7)
        ]
        return {
            "total": total,
            "benign": counts.get("benign", 0),
            "suspicious": counts.get("suspicious", 0),
            "malicious": counts.get("malicious", 0),
            "processing": self.db.scalar(
                select(func.count(Analysis.id)).where(Analysis.status == "processing")
            )
            or 0,
            "recent": recent,
            "recent_threats": threats,
            "activity": activity,
        }
