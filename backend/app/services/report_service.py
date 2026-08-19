from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from app.database.models import Analysis, Report
from app.integrations.ollama_client import OllamaClient, ReportGenerationError
from app.reporting.pdf_generator import PDFGenerationError, generate_pdf
from app.repositories.report_repository import ReportRepository


logger = logging.getLogger(__name__)


class ReportService:
    def __init__(self, db: Session, ollama: OllamaClient, report_dir: Path) -> None:
        self.repository = ReportRepository(db)
        self.ollama = ollama
        self.report_dir = report_dir

    def generate(self, analysis: Analysis, technical_data: dict[str, Any]) -> Report:
        report_record = self.repository.create(
            analysis_id=analysis.id, generation_status="generating"
        )
        try:
            structured = self.ollama.generate_report(self._evidence(analysis, technical_data))
            report_record.report_json = structured.model_dump_json()
            report_record.generation_status = "structured"
            self.repository.save(report_record)
        except ReportGenerationError as exc:
            report_record.generation_status = "failed"
            report_record.error_message = str(exc)[:2000]
            logger.warning(
                "report generation unavailable",
                extra={"event": "report_failed", "analysis_id": analysis.id, "status": "failed"},
            )
            return self.repository.save(report_record)

        try:
            pdf_path = self.report_dir / f"analysis-{analysis.id}.pdf"
            generate_pdf(analysis, structured, pdf_path)
            report_record.pdf_path = str(pdf_path)
            report_record.generation_status = "completed"
            logger.info(
                "report generated",
                extra={"event": "report_completed", "analysis_id": analysis.id, "status": "completed"},
            )
        except (PDFGenerationError, ValueError) as exc:
            report_record.generation_status = "pdf_failed"
            report_record.error_message = str(exc)[:2000]
            logger.warning(
                "PDF generation failed",
                extra={"event": "pdf_failed", "analysis_id": analysis.id, "status": "failed"},
            )
        return self.repository.save(report_record)

    @staticmethod
    def _evidence(analysis: Analysis, technical: dict[str, Any]) -> dict[str, Any]:
        return {
            "file": {
                "name": analysis.original_filename,
                "sha256": analysis.sha256,
                "size_bytes": analysis.file_size,
                "source": analysis.source,
            },
            "model_result": {
                "final_classification": analysis.classification,
                "score": analysis.score,
                "model": analysis.model_name,
                "model_version": analysis.model_version,
            },
            "detection_layers": technical.get("detection", {}),
            "pe_metadata": {
                key: technical.get(key)
                for key in (
                    "architecture",
                    "compiled_at",
                    "entry_point",
                    "image_base",
                    "subsystem",
                    "number_of_sections",
                    "overall_entropy",
                )
            },
            "sections": technical.get("sections", [])[:32],
            "imports": technical.get("imports", [])[:60],
            "exports": technical.get("exports", [])[:100],
            "selected_printable_strings": technical.get("strings", [])[:80],
            "evidence_note": (
                "All items are static observations. Imports and strings indicate potential, "
                "not confirmed runtime behavior."
            ),
        }
