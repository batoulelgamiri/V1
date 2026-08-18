from __future__ import annotations

from functools import lru_cache

from app.core.config import get_settings
from app.engines.xgboost_engine import XGBoostDetectionEngine


@lru_cache
def get_detection_engine() -> XGBoostDetectionEngine:
    settings = get_settings()
    return XGBoostDetectionEngine(
        model_path=settings.model_path,
        expected_sha256=settings.model_expected_sha256,
        suspicious_threshold=settings.suspicious_threshold,
        malicious_threshold=settings.malicious_threshold,
    )

