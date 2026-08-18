import pytest

from app.engines.xgboost_engine import classify_score


@pytest.mark.parametrize(
    ("score", "expected"),
    [(0.0, "benign"), (0.499, "benign"), (0.5, "suspicious"), (0.799, "suspicious"), (0.8, "malicious"), (1.0, "malicious")],
)
def test_classification_thresholds(score: float, expected: str) -> None:
    assert classify_score(score, 0.5, 0.8) == expected


def test_out_of_range_score_is_rejected() -> None:
    with pytest.raises(ValueError):
        classify_score(1.1, 0.5, 0.8)

