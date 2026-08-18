from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


Confidence = Literal["low", "medium", "high"]
RiskLevel = Literal["low", "medium", "high", "critical"]


class ConfirmedIndicator(BaseModel):
    indicator: str = Field(min_length=1, max_length=300)
    evidence: str = Field(min_length=1, max_length=1000)


class SuspectedCapability(BaseModel):
    capability: str = Field(min_length=1, max_length=300)
    confidence: Confidence
    evidence: list[str] = Field(default_factory=list, max_length=20)


class MitreMapping(BaseModel):
    technique_id: str = Field(pattern=r"^T\d{4}(?:\.\d{3})?$")
    technique_name: str = Field(min_length=1, max_length=200)
    confidence: Confidence
    evidence: str = Field(min_length=1, max_length=1000)


class StructuredReport(BaseModel):
    executive_summary: str = Field(min_length=1, max_length=4000)
    classification_result: Literal["suspicious", "malicious"]
    risk_level: RiskLevel
    confirmed_indicators: list[ConfirmedIndicator] = Field(default_factory=list, max_length=100)
    suspected_capabilities: list[SuspectedCapability] = Field(default_factory=list, max_length=50)
    mitre_attack: list[MitreMapping] = Field(default_factory=list, max_length=50)
    recommendations: list[str] = Field(min_length=1, max_length=50)
    limitations: list[str] = Field(min_length=1, max_length=30)


class ReportResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    analysis_id: int
    generation_status: str
    report: StructuredReport | None
    error_message: str | None
    pdf_available: bool
    created_at: datetime

