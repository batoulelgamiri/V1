from __future__ import annotations

from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.database.models import Base
from app.engines.xgboost_engine import DetectionResult
from app.engines.yara_engine import YaraMatch, YaraScanResult
from app.services.analysis_service import AnalysisService


class FakeEngine:
    model_version = "fake-model-ember-v2"

    def __init__(self) -> None:
        self.calls = 0

    def analyze(self, _path: Path) -> DetectionResult:
        self.calls += 1
        return DetectionResult(0.12, "benign", "fake-model", self.model_version)


class FakeYaraEngine:
    ruleset_version = "yara-fixture"
    cache_version = "yara-fixture-ready"

    def __init__(self, verdict: str | None = None) -> None:
        self.verdict = verdict
        self.calls = 0

    def scan(self, _path: Path) -> YaraScanResult:
        self.calls += 1
        matches = ()
        if self.verdict:
            matches = (
                YaraMatch(
                    rule="Fixture_Rule",
                    namespace="fixture",
                    tags=("test",),
                    severity="high",
                    confidence="high",
                    verdict=self.verdict,  # type: ignore[arg-type]
                    family="Fixture",
                    description="Test evidence",
                    reference=None,
                ),
            )
        return YaraScanResult(
            status="completed", ruleset_version=self.ruleset_version, matches=matches
        )


def test_valid_pe_pipeline_and_duplicate_cache(minimal_pe: Path, tmp_path: Path) -> None:
    engine_db = create_engine(f"sqlite:///{(tmp_path / 'integration.db').as_posix()}")
    Base.metadata.create_all(engine_db)
    fake_engine = FakeEngine()
    fake_yara = FakeYaraEngine()
    settings = Settings(
        database_url=f"sqlite:///{(tmp_path / 'integration.db').as_posix()}",
        storage_dir=tmp_path / "storage",
    )
    with Session(engine_db, expire_on_commit=False) as db:
        service = AnalysisService(db, settings, fake_engine, fake_yara)  # type: ignore[arg-type]
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
    assert fake_yara.calls == 1


def test_yara_can_override_a_benign_model_verdict(minimal_pe: Path, tmp_path: Path) -> None:
    engine_db = create_engine(f"sqlite:///{(tmp_path / 'yara-integration.db').as_posix()}")
    Base.metadata.create_all(engine_db)
    settings = Settings(
        database_url=f"sqlite:///{(tmp_path / 'yara-integration.db').as_posix()}",
        storage_dir=tmp_path / "storage",
        ollama_base_url="http://127.0.0.1:1",
        ollama_timeout_seconds=0.1,
    )
    with Session(engine_db, expire_on_commit=False) as db:
        service = AnalysisService(
            db,
            settings,
            FakeEngine(),  # type: ignore[arg-type]
            FakeYaraEngine("malicious"),  # type: ignore[arg-type]
        )
        result = service.analyze_file(
            minimal_pe,
            original_filename="known-malware.exe",
            file_size=minimal_pe.stat().st_size,
            source="manual",
        )

    assert result.status == "completed"
    assert result.classification == "malicious"
    assert result.score == 0.12
    assert result.technical_data is not None
    assert '"yara"' in result.technical_data
