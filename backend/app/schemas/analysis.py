from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


AnalysisSource = Literal["manual", "wazuh"]
Classification = Literal["benign", "suspicious", "malicious"]


class WazuhMetadata(BaseModel):
    endpoint_id: str = Field(min_length=1, max_length=255)
    endpoint_name: str = Field(min_length=1, max_length=255)
    file_path: str = Field(min_length=1, max_length=2048)


class AnalysisListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    sha256: str
    original_filename: str
    file_size: int
    source: str
    endpoint_id: str | None
    endpoint_name: str | None
    file_path: str | None
    created_at: datetime
    status: str
    classification: str | None
    score: float | None
    model_name: str
    model_version: str
    cached_from_analysis_id: int | None
    report_available: bool = False
    report_status: str | None = None


class AnalysisDetail(AnalysisListItem):
    file_type: str
    technical_data: dict[str, Any] | None
    error_message: str | None


class AnalysisPage(BaseModel):
    items: list[AnalysisListItem]
    page: int
    page_size: int
    total: int
    pages: int


class Thresholds(BaseModel):
    suspicious: float
    malicious: float


class PublicSettings(BaseModel):
    app_name: str
    environment: str
    max_file_size_mb: int
    thresholds: Thresholds
    model_name: str
    model_path_configured: bool
    ollama_model: str


class ErrorResponse(BaseModel):
    detail: str
    code: str | None = None

