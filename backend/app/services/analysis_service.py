from __future__ import annotations

import json
import logging
from pathlib import Path

from sqlalchemy.orm import Session

from app.analyzers.pe_parser import parse_pe, validate_pe
from app.core.config import Settings
from app.database.models import Analysis
from app.engines.xgboost_engine import MODEL_NAME, ModelUnavailableError, XGBoostDetectionEngine
from app.engines.yara_engine import (
    YaraDetectionEngine,
    YaraScanError,
    YaraScanResult,
    YaraUnavailableError,
)
from app.integrations.ollama_client import OllamaClient
from app.repositories.analysis_repository import AnalysisRepository
from app.repositories.endpoint_repository import EndpointRepository
from app.repositories.report_repository import ReportRepository
from app.services.hash_service import sha256_file
from app.services.report_service import ReportService
from app.services.verdict_service import combine_verdict


logger = logging.getLogger(__name__)


class AnalysisService:
    def __init__(
        self,
        db: Session,
        settings: Settings,
        engine: XGBoostDetectionEngine | None = None,
        yara_engine: YaraDetectionEngine | None = None,
    ) -> None:
        self.db = db
        self.settings = settings
        self.repository = AnalysisRepository(db)
        self.report_repository = ReportRepository(db)
        self.engine = engine or XGBoostDetectionEngine(
            model_path=settings.model_path,
            expected_sha256=settings.model_expected_sha256,
            suspicious_threshold=settings.suspicious_threshold,
            malicious_threshold=settings.malicious_threshold,
        )
        self.yara_engine = yara_engine or YaraDetectionEngine(
            rules_dir=settings.resolved_yara_rules_dir,
            timeout_seconds=settings.yara_timeout_seconds,
            enabled=settings.yara_enabled,
        )
        self.pipeline_version = f"{self.engine.model_version}+{self.yara_engine.cache_version}"

    def analyze_file(
        self,
        path: Path,
        *,
        original_filename: str,
        file_size: int,
        source: str,
        endpoint_id: str | None = None,
        endpoint_name: str | None = None,
        file_path: str | None = None,
    ) -> Analysis:
        validate_pe(path)
        digest = sha256_file(path)
        if source == "wazuh" and endpoint_id and endpoint_name:
            EndpointRepository(self.db).upsert(endpoint_id, endpoint_name)

        cached = self.repository.find_cached(digest, self.pipeline_version)
        if cached:
            return self._record_cache_hit(
                cached,
                original_filename=original_filename,
                file_size=file_size,
                source=source,
                endpoint_id=endpoint_id,
                endpoint_name=endpoint_name,
                file_path=file_path,
            )

        analysis = self.repository.create(
            sha256=digest,
            original_filename=original_filename,
            file_size=file_size,
            file_type="Windows Portable Executable",
            source=source,
            endpoint_id=endpoint_id,
            endpoint_name=endpoint_name,
            file_path=file_path,
            status="processing",
            model_name=MODEL_NAME,
            model_version=self.pipeline_version,
        )
        logger.info(
            "analysis started",
            extra={"event": "analysis_started", "analysis_id": analysis.id, "source": source},
        )
        try:
            technical = parse_pe(path)
            model_result = self.engine.analyze(path)
            yara_result = self._scan_yara(path)
            verdict = combine_verdict(model_result, yara_result)
            technical["detection"] = {
                "final_verdict": verdict.as_dict(),
                "xgboost": {
                    "classification": model_result.classification,
                    "malicious_probability": model_result.score,
                    "model": model_result.model_name,
                    "model_version": model_result.model_version,
                },
                "yara": yara_result.as_dict(),
            }
            analysis.technical_data = json.dumps(technical, ensure_ascii=False)
            analysis.classification = verdict.classification
            analysis.score = model_result.score
            analysis.model_name = model_result.model_name
            analysis.model_version = self.pipeline_version
            analysis.status = "completed"
            self.repository.save(analysis)
            logger.info(
                "analysis completed",
                extra={
                    "event": "analysis_completed",
                    "analysis_id": analysis.id,
                    "source": source,
                    "classification": verdict.classification,
                    "status": "completed",
                },
            )
            if verdict.classification in {"suspicious", "malicious"}:
                ollama = OllamaClient(
                    self.settings.ollama_base_url,
                    self.settings.ollama_model,
                    self.settings.ollama_timeout_seconds,
                )
                ReportService(
                    self.db,
                    ollama,
                    self.settings.resolved_storage_dir / "reports",
                ).generate(analysis, technical)
            return self.repository.get(analysis.id) or analysis
        except ModelUnavailableError as exc:
            analysis.status = "failed"
            analysis.error_message = str(exc)[:2000]
            logger.error(
                "model unavailable",
                extra={"event": "analysis_failed", "analysis_id": analysis.id, "status": "failed"},
            )
            return self.repository.save(analysis)
        except Exception as exc:
            analysis.status = "failed"
            analysis.error_message = f"Static analysis failed: {exc}"[:2000]
            logger.exception(
                "analysis failed",
                extra={"event": "analysis_failed", "analysis_id": analysis.id, "status": "failed"},
            )
            return self.repository.save(analysis)

    def _scan_yara(self, path: Path) -> YaraScanResult:
        try:
            return self.yara_engine.scan(path)
        except YaraUnavailableError as exc:
            logger.warning(
                "YARA unavailable",
                extra={"event": "yara_unavailable", "status": "unavailable"},
            )
            return YaraScanResult.unavailable(self.yara_engine.ruleset_version, str(exc))
        except YaraScanError as exc:
            logger.warning(
                "YARA scan failed",
                extra={"event": "yara_failed", "status": "failed"},
            )
            return YaraScanResult.failed(self.yara_engine.ruleset_version, str(exc))

    def _record_cache_hit(self, cached: Analysis, **metadata) -> Analysis:
        duplicate = self.repository.create(
            sha256=cached.sha256,
            original_filename=metadata["original_filename"],
            file_size=metadata["file_size"],
            file_type=cached.file_type,
            source=metadata["source"],
            endpoint_id=metadata.get("endpoint_id"),
            endpoint_name=metadata.get("endpoint_name"),
            file_path=metadata.get("file_path"),
            status="completed",
            classification=cached.classification,
            score=cached.score,
            model_name=cached.model_name,
            model_version=cached.model_version,
            technical_data=cached.technical_data,
            cached_from_analysis_id=cached.id,
        )
        if cached.report:
            self.report_repository.create(
                analysis_id=duplicate.id,
                report_json=cached.report.report_json,
                pdf_path=cached.report.pdf_path,
                generation_status="cached",
                error_message=cached.report.error_message,
            )
        logger.info(
            "duplicate analysis reused",
            extra={"event": "analysis_cache_hit", "analysis_id": duplicate.id, "source": duplicate.source},
        )
        return self.repository.get(duplicate.id) or duplicate
