from __future__ import annotations

from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.database.models import Base
from app.engines.xgboost_engine import DetectionResult
from app.services.analysis_service import AnalysisService


class FakeEngine:
    model_version = "fake-model-ember-v2"

    def __init__(self) -> None:
        self.calls = 0

    def analyze(self, _path: Path) -> DetectionResult:
        self.calls += 1
        return DetectionResult(0.12, "benign", "fake-model", self.model_version)


def test_valid_pe_pipeline_and_duplicate_cache(minimal_pe: Path, tmp_path: Path) -> None:
    engine_db = create_engine(f"sqlite:///{(tmp_path / 'integration.db').as_posix()}")
    Base.metadata.create_all(engine_db)
    fake_engine = FakeEngine()
    settings = Settings(
        database_url=f"sqlite:///{(tmp_path / 'integration.db').as_posix()}",
        storage_dir=tmp_path / "storage",
    )
    with Session(engine_db, expire_on_commit=False) as db:
        service = AnalysisService(db, settings, fake_engine)  # type: ignore[arg-type]
        first = service.analyze_file(
            minimal_pe,
            original_filename="first.exe",
            file_size=minimal_pe.stat().st_size,
            source="manual",
        )
        second = service.analyze_file(
            minimal_pe,
            original_filename="second.exe",
            file_size=minimal_pe.stat().st_size,
            source="wazuh",
            endpoint_id="endpoint-01",
            endpoint_name="LAB-01",
            file_path=r"C:\\Samples\\second.exe",
        )
    assert first.status == "completed"
    assert first.classification == "benign"
    assert first.technical_data
    assert second.cached_from_analysis_id == first.id
    assert second.source == "wazuh"
    assert fake_engine.calls == 1

