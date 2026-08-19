from __future__ import annotations

from pathlib import Path

from app.engines.xgboost_engine import DetectionResult
from app.engines.yara_engine import YaraDetectionEngine, YaraMatch, YaraScanResult
from app.services.verdict_service import combine_verdict


def write_rule(path: Path, verdict: str = "malicious") -> None:
    path.write_text(
        f'''rule Test_PE_Signature : test
{{
    meta:
        description = "Test-only PE signature"
        family = "Fixture"
        severity = "high"
        confidence = "high"
        aegis_verdict = "{verdict}"
    condition:
        uint16(0) == 0x5a4d
}}
''',
        encoding="utf-8",
    )


def test_yara_engine_compiles_and_returns_normalized_evidence(
    minimal_pe: Path, tmp_path: Path
) -> None:
    rules_dir = tmp_path / "rules"
    rules_dir.mkdir()
    write_rule(rules_dir / "test.yar")
    engine = YaraDetectionEngine(rules_dir=rules_dir, timeout_seconds=5)

    result = engine.scan(minimal_pe)

    assert engine.available is True
    assert result.status == "completed"
    assert result.matches[0].rule == "Test_PE_Signature"
    assert result.matches[0].family == "Fixture"
    assert result.matches[0].verdict == "malicious"
    assert result.ruleset_version.startswith("yara-")


def test_ruleset_fingerprint_changes_with_rule_content(tmp_path: Path) -> None:
    rules_dir = tmp_path / "rules"
    rules_dir.mkdir()
    rule_path = rules_dir / "test.yar"
    write_rule(rule_path, "suspicious")
    first = YaraDetectionEngine(rules_dir).ruleset_version
    write_rule(rule_path, "malicious")
    second = YaraDetectionEngine(rules_dir).ruleset_version
    assert first != second


def test_malicious_yara_verdict_overrides_benign_model() -> None:
    model = DetectionResult(0.445, "benign", "test", "test-v1")
    match = YaraMatch(
        rule="Known_Malware",
        namespace="known",
        tags=("ransomware",),
        severity="critical",
        confidence="high",
        verdict="malicious",
        family="Fixture",
        description="Known malicious fixture",
        reference=None,
    )
    yara_result = YaraScanResult(
        status="completed", ruleset_version="yara-test", matches=(match,)
    )

    verdict = combine_verdict(model, yara_result)

    assert verdict.classification == "malicious"
    assert verdict.sources == ("yara", "xgboost")


def test_non_authoritative_yara_match_does_not_override_model() -> None:
    model = DetectionResult(0.12, "benign", "test", "test-v1")
    match = YaraMatch(
        rule="Informational_PE",
        namespace="info",
        tags=(),
        severity="low",
        confidence="low",
        verdict=None,
        family=None,
        description="Informational only",
        reference=None,
    )
    yara_result = YaraScanResult(
        status="completed", ruleset_version="yara-test", matches=(match,)
    )

    assert combine_verdict(model, yara_result).classification == "benign"
