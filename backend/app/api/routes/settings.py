from __future__ import annotations

from fastapi import APIRouter, Depends

from app.core.config import Settings, get_settings
from app.api.dependencies import get_yara_engine
from app.engines.xgboost_engine import MODEL_NAME
from app.engines.yara_engine import YaraDetectionEngine
from app.schemas.analysis import PublicSettings, Thresholds


router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("/public", response_model=PublicSettings)
def public_settings(
    settings: Settings = Depends(get_settings),
    yara_engine: YaraDetectionEngine = Depends(get_yara_engine),
) -> PublicSettings:
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
        yara_enabled=settings.yara_enabled,
        yara_available=yara_engine.available,
        yara_ruleset_version=yara_engine.ruleset_version,
    )
