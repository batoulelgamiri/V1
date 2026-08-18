from __future__ import annotations

import json
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, Header, HTTPException, Query, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.api.dependencies import get_detection_engine
from app.core.config import Settings, get_settings
from app.core.security import api_keys_match
from app.database.models import Analysis
from app.database.session import get_db
from app.engines.xgboost_engine import XGBoostDetectionEngine
from app.repositories.analysis_repository import AnalysisRepository
from app.repositories.report_repository import ReportRepository
from app.schemas.analysis import AnalysisDetail, AnalysisListItem, AnalysisPage
from app.schemas.report import ReportResponse, StructuredReport
from app.services.analysis_service import AnalysisService
from app.services.upload_service import UploadValidationError, save_upload_limited


router = APIRouter(prefix="/analyses", tags=["analyses"])


def to_list_item(analysis: Analysis) -> AnalysisListItem:
    report = analysis.report
    return AnalysisListItem(
        id=analysis.id,
        sha256=analysis.sha256,
        original_filename=analysis.original_filename,
        file_size=analysis.file_size,
        source=analysis.source,
        endpoint_id=analysis.endpoint_id,
        endpoint_name=analysis.endpoint_name,
        file_path=analysis.file_path,
        created_at=analysis.created_at,
        status=analysis.status,
        classification=analysis.classification,
        score=analysis.score,
        model_name=analysis.model_name,
        model_version=analysis.model_version,
        cached_from_analysis_id=analysis.cached_from_analysis_id,
        report_available=bool(report and report.report_json),
        report_status=report.generation_status if report else None,
    )


def to_detail(analysis: Analysis) -> AnalysisDetail:
    item = to_list_item(analysis).model_dump()
    technical_data = None
    if analysis.technical_data:
        try:
            technical_data = json.loads(analysis.technical_data)
        except json.JSONDecodeError:
            technical_data = None
    return AnalysisDetail(
        **item,
        file_type=analysis.file_type,
        technical_data=technical_data,
        error_message=analysis.error_message,
    )


async def _analyze_upload(
    *,
    upload: UploadFile,
    source: str,
    db: Session,
    settings: Settings,
    engine: XGBoostDetectionEngine,
    endpoint_id: str | None = None,
    endpoint_name: str | None = None,
    file_path: str | None = None,
) -> AnalysisDetail:
    temp_dir = settings.resolved_storage_dir / "incoming"
    try:
        path, file_size, filename = await save_upload_limited(
            upload, temp_dir, settings.max_file_size_bytes
        )
    except UploadValidationError as exc:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail=str(exc)) from exc
    try:
        analysis = AnalysisService(db, settings, engine).analyze_file(
            path,
            original_filename=filename,
            file_size=file_size,
            source=source,
            endpoint_id=endpoint_id,
            endpoint_name=endpoint_name,
            file_path=file_path,
        )
        return to_detail(analysis)
    finally:
        path.unlink(missing_ok=True)


@router.post("/upload", response_model=AnalysisDetail)
async def upload_analysis(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    engine: XGBoostDetectionEngine = Depends(get_detection_engine),
) -> AnalysisDetail:
    return await _analyze_upload(
        upload=file, source="manual", db=db, settings=settings, engine=engine
    )


@router.post("/wazuh", response_model=AnalysisDetail)
async def wazuh_analysis(
    file: UploadFile = File(...),
    endpoint_id: str = Form(..., min_length=1, max_length=255),
    endpoint_name: str = Form(..., min_length=1, max_length=255),
    file_path: str = Form(..., min_length=1, max_length=2048),
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    engine: XGBoostDetectionEngine = Depends(get_detection_engine),
) -> AnalysisDetail:
    if not api_keys_match(x_api_key, settings.wazuh_ingest_api_key):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Wazuh ingest API key.")
    return await _analyze_upload(
        upload=file,
        source="wazuh",
        db=db,
        settings=settings,
        engine=engine,
        endpoint_id=endpoint_id,
        endpoint_name=endpoint_name,
        file_path=file_path,
    )


@router.get("", response_model=AnalysisPage)
def list_analyses(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    classification: str | None = Query(default=None, pattern="^(benign|suspicious|malicious)$"),
    source: str | None = Query(default=None, pattern="^(manual|wazuh)$"),
    search: str | None = Query(default=None, max_length=255),
    db: Session = Depends(get_db),
) -> AnalysisPage:
    items, total, pages = AnalysisRepository(db).list(
        page=page,
        page_size=page_size,
        classification=classification,
        source=source,
        search=search,
    )
    return AnalysisPage(
        items=[to_list_item(item) for item in items],
        page=page,
        page_size=page_size,
        total=total,
        pages=pages,
    )


@router.get("/{analysis_id}", response_model=AnalysisDetail)
def get_analysis(analysis_id: int, db: Session = Depends(get_db)) -> AnalysisDetail:
    analysis = AnalysisRepository(db).get(analysis_id)
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found.")
    return to_detail(analysis)


@router.get("/{analysis_id}/report", response_model=ReportResponse)
def get_report(analysis_id: int, db: Session = Depends(get_db)) -> ReportResponse:
    report = ReportRepository(db).get_for_analysis(analysis_id)
    if not report:
        raise HTTPException(status_code=404, detail="No report is available for this analysis.")
    structured = StructuredReport.model_validate_json(report.report_json) if report.report_json else None
    return ReportResponse(
        id=report.id,
        analysis_id=report.analysis_id,
        generation_status=report.generation_status,
        report=structured,
        error_message=report.error_message,
        pdf_available=bool(report.pdf_path and Path(report.pdf_path).is_file()),
        created_at=report.created_at,
    )


@router.get("/{analysis_id}/report/pdf")
def download_report_pdf(analysis_id: int, db: Session = Depends(get_db)) -> FileResponse:
    report = ReportRepository(db).get_for_analysis(analysis_id)
    if not report or not report.pdf_path:
        raise HTTPException(status_code=404, detail="No PDF report is available for this analysis.")
    path = Path(report.pdf_path)
    if not path.is_file():
        raise HTTPException(status_code=404, detail="The PDF report file is unavailable.")
    return FileResponse(
        path,
        media_type="application/pdf",
        filename=f"aegis-analysis-{analysis_id}.pdf",
    )

