from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.database.models import Analysis
from app.integrations.ollama_client import ReportGenerationError, parse_structured_report
from app.reporting.pdf_generator import generate_pdf
from app.schemas.report import StructuredReport


def valid_report_payload() -> dict:
    return {
        "executive_summary": "Static indicators warrant analyst review.",
        "classification_result": "suspicious",
        "risk_level": "medium",
        "confirmed_indicators": [{"indicator": "High entropy section", "evidence": ".text entropy is 7.4"}],
        "suspected_capabilities": [{"capability": "Packing", "confidence": "medium", "evidence": ["High entropy"]}],
        "mitre_attack": [],
        "recommendations": ["Do not execute the sample."],
        "limitations": ["Static analysis cannot confirm runtime behavior."],
    }


def test_llm_response_validation() -> None:
    parsed = parse_structured_report(json.dumps(valid_report_payload()))
    assert parsed.risk_level == "medium"


def test_malformed_llm_response_is_rejected() -> None:
    with pytest.raises(ReportGenerationError):
        parse_structured_report("not json")


def test_pdf_generation_uses_validated_input(tmp_path: Path) -> None:
    analysis = Analysis(
        id=7,
        sha256="a" * 64,
        original_filename="sample.exe",
        file_size=1024,
        file_type="Windows Portable Executable",
        source="manual",
        status="completed",
        classification="suspicious",
        score=0.72,
        model_name="test-model",
        model_version="test-v1",
    )
    report = StructuredReport.model_validate(valid_report_payload())
    path = generate_pdf(analysis, report, tmp_path / "report.pdf")
    assert path.read_bytes().startswith(b"%PDF")


def test_pdf_rejects_mismatched_classification(tmp_path: Path) -> None:
    analysis = Analysis(
        id=8,
        sha256="b" * 64,
        original_filename="sample.exe",
        file_size=1024,
        file_type="Windows Portable Executable",
        source="manual",
        status="completed",
        classification="malicious",
        score=0.92,
        model_name="test-model",
        model_version="test-v1",
    )
    with pytest.raises(ValueError):
        generate_pdf(analysis, StructuredReport.model_validate(valid_report_payload()), tmp_path / "bad.pdf")

