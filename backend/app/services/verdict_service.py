from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.engines.xgboost_engine import DetectionResult
from app.engines.yara_engine import YaraScanResult


@dataclass(frozen=True)
class CombinedVerdict:
    classification: str
    sources: tuple[str, ...]
    reason: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "classification": self.classification,
            "sources": list(self.sources),
            "reason": self.reason,
        }


def combine_verdict(
    model_result: DetectionResult, yara_result: YaraScanResult
) -> CombinedVerdict:
    if "malicious" in yara_result.verdicts:
        return CombinedVerdict(
            classification="malicious",
            sources=("yara", "xgboost"),
            reason="A YARA rule explicitly marked the sample as malicious.",
        )
    if "suspicious" in yara_result.verdicts and model_result.classification == "benign":
        return CombinedVerdict(
            classification="suspicious",
            sources=("yara", "xgboost"),
            reason="A YARA rule supplied suspicious evidence above the model-only verdict.",
        )
    return CombinedVerdict(
        classification=model_result.classification,
        sources=("xgboost",) if not yara_result.matches else ("xgboost", "yara"),
        reason="No authoritative YARA verdict overrode the XGBoost classification.",
    )
