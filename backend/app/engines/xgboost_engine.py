from __future__ import annotations

import hashlib
import logging
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import xgboost as xgb

from app.analyzers.feature_extractor import EmberV2FeatureExtractor


logger = logging.getLogger(__name__)
MODEL_NAME = "Pugazh24/X-MalForensics-XGBoost"


class ModelUnavailableError(RuntimeError):
    pass


@dataclass(frozen=True)
class DetectionResult:
    score: float
    classification: str
    model_name: str
    model_version: str


def classify_score(score: float, suspicious_threshold: float, malicious_threshold: float) -> str:
    if not 0 <= score <= 1:
        raise ValueError("Model score must be in the range [0, 1]")
    if score >= malicious_threshold:
        return "malicious"
    if score >= suspicious_threshold:
        return "suspicious"
    return "benign"


class XGBoostDetectionEngine:
    def __init__(
        self,
        *,
        model_path: Path,
        expected_sha256: str,
        suspicious_threshold: float,
        malicious_threshold: float,
    ) -> None:
        self.model_path = model_path
        self.expected_sha256 = expected_sha256
        self.suspicious_threshold = suspicious_threshold
        self.malicious_threshold = malicious_threshold
        self._model: xgb.XGBClassifier | None = None
        self._extractor: EmberV2FeatureExtractor | None = None
        digest = expected_sha256[:12] if expected_sha256 else "unverified"
        self.model_version = f"hf-{digest}-ember-v2"

    @property
    def available(self) -> bool:
        try:
            self._ensure_loaded()
            return True
        except ModelUnavailableError:
            return False

    def _ensure_loaded(self) -> None:
        if self._model is not None and self._extractor is not None:
            return
        if not self.model_path.is_file():
            raise ModelUnavailableError(
                f"Model file is missing at {self.model_path}. Run backend/scripts/setup_model.py."
            )
        digest = hashlib.sha256(self.model_path.read_bytes()).hexdigest()
        if self.expected_sha256 and digest != self.expected_sha256:
            raise ModelUnavailableError("Model SHA-256 does not match the verified public artifact.")
        try:
            extractor = EmberV2FeatureExtractor()
            model = xgb.XGBClassifier()
            model.load_model(self.model_path)
            booster_features = int(model.get_booster().num_features())
            if booster_features != extractor.expected_dimension:
                raise ModelUnavailableError(
                    f"Model expects {booster_features} features; EMBER v2 provides 2381."
                )
        except ModelUnavailableError:
            raise
        except Exception as exc:
            raise ModelUnavailableError(f"Unable to load the verified model: {exc}") from exc
        self._extractor = extractor
        self._model = model
        logger.info("model loaded", extra={"event": "model_loaded", "status": "available"})

    def analyze(self, path: Path) -> DetectionResult:
        self._ensure_loaded()
        assert self._extractor is not None and self._model is not None
        features = self._extractor.extract(path)
        probabilities = self._model.predict_proba(np.asarray([features], dtype=np.float32))
        score = float(probabilities[0][1])
        classification = classify_score(
            score, self.suspicious_threshold, self.malicious_threshold
        )
        return DetectionResult(
            score=score,
            classification=classification,
            model_name=MODEL_NAME,
            model_version=self.model_version,
        )

