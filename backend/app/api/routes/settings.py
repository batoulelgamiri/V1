from __future__ import annotations

from fastapi import APIRouter, Depends

from app.core.config import Settings, get_settings
from app.engines.xgboost_engine import MODEL_NAME
from app.schemas.analysis import PublicSettings, Thresholds


router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("/public", response_model=PublicSettings)
def public_settings(settings: Settings = Depends(get_settings)) -> PublicSettings:
    return PublicSettings(
        app_name=settings.app_name,
        environment=settings.app_env,
        max_file_size_mb=settings.max_file_size_mb,
        thresholds=Thresholds(
            suspicious=settings.suspicious_threshold,
            malicious=settings.malicious_threshold,
        ),
        model_name=MODEL_NAME,
        model_path_configured=settings.model_path.is_file(),
        ollama_model=settings.ollama_model,
    )

