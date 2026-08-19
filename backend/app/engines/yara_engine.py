from __future__ import annotations

import hashlib
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal


logger = logging.getLogger(__name__)
YaraVerdict = Literal["suspicious", "malicious"]


class YaraUnavailableError(RuntimeError):
    pass


class YaraScanError(RuntimeError):
    pass


@dataclass(frozen=True)
class YaraMatch:
    rule: str
    namespace: str
    tags: tuple[str, ...]
    severity: str | None
    confidence: str | None
    verdict: YaraVerdict | None
    family: str | None
    description: str | None
    reference: str | None
    matched_strings: tuple[str, ...] = ()

    def as_dict(self) -> dict[str, Any]:
        return {
            "rule": self.rule,
            "namespace": self.namespace,
            "tags": list(self.tags),
            "severity": self.severity,
            "confidence": self.confidence,
            "verdict": self.verdict,
            "family": self.family,
            "description": self.description,
            "reference": self.reference,
            "matched_strings": list(self.matched_strings),
        }


@dataclass(frozen=True)
class YaraScanResult:
    status: Literal["completed", "unavailable", "error"]
    ruleset_version: str
    matches: tuple[YaraMatch, ...] = ()
    error: str | None = None

    @property
    def verdicts(self) -> set[YaraVerdict]:
        return {match.verdict for match in self.matches if match.verdict is not None}

    def as_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "ruleset_version": self.ruleset_version,
            "match_count": len(self.matches),
            "matches": [match.as_dict() for match in self.matches],
            "error": self.error,
        }

    @classmethod
    def unavailable(cls, ruleset_version: str, error: str) -> "YaraScanResult":
        return cls(status="unavailable", ruleset_version=ruleset_version, error=error[:1000])

    @classmethod
    def failed(cls, ruleset_version: str, error: str) -> "YaraScanResult":
        return cls(status="error", ruleset_version=ruleset_version, error=error[:1000])


@dataclass
class YaraDetectionEngine:
    rules_dir: Path
    timeout_seconds: int = 10
    enabled: bool = True
    _rules: Any | None = field(default=None, init=False, repr=False)
    _load_error: str | None = field(default=None, init=False, repr=False)

    def __post_init__(self) -> None:
        self.rules_dir = self.rules_dir.resolve()
        self._rule_files = tuple(
            sorted(
                (
                    path
                    for path in self.rules_dir.rglob("*")
                    if path.is_file() and path.suffix.lower() in {".yar", ".yara"}
                ),
                key=lambda path: path.as_posix().lower(),
            )
        )
        self.ruleset_version = self._fingerprint()

    def _fingerprint(self) -> str:
        if not self.enabled:
            return "yara-disabled"
        digest = hashlib.sha256()
        for path in self._rule_files:
            digest.update(path.relative_to(self.rules_dir).as_posix().encode("utf-8"))
            digest.update(b"\x00")
            digest.update(path.read_bytes())
            digest.update(b"\x00")
        return f"yara-{digest.hexdigest()[:12]}" if self._rule_files else "yara-no-rules"

    @property
    def available(self) -> bool:
        try:
            self._ensure_loaded()
            return True
        except YaraUnavailableError:
            return False

    @property
    def error(self) -> str | None:
        if self.available:
            return None
        return self._load_error

    @property
    def cache_version(self) -> str:
        status = "ready" if self.available else "unavailable"
        return f"{self.ruleset_version}-{status}"

    def _ensure_loaded(self) -> None:
        if self._rules is not None:
            return
        if self._load_error is not None:
            raise YaraUnavailableError(self._load_error)
        if not self.enabled:
            self._load_error = "YARA scanning is disabled by configuration."
            raise YaraUnavailableError(self._load_error)
        if not self._rule_files:
            self._load_error = f"No YARA rules were found in {self.rules_dir}."
            raise YaraUnavailableError(self._load_error)
        try:
            import yara

            namespaces = {
                f"rule_{index}_{path.stem}": str(path)
                for index, path in enumerate(self._rule_files)
            }
            self._rules = yara.compile(filepaths=namespaces, error_on_warning=False)
        except ImportError as exc:
            self._load_error = "yara-python is not installed. Install backend requirements."
            raise YaraUnavailableError(self._load_error) from exc
        except Exception as exc:
            self._load_error = f"Unable to compile the YARA ruleset: {exc}"
            raise YaraUnavailableError(self._load_error) from exc
        logger.info(
            "YARA rules loaded",
            extra={"event": "yara_loaded", "status": "available"},
        )

    def scan(self, path: Path) -> YaraScanResult:
        self._ensure_loaded()
        assert self._rules is not None
        try:
            raw_matches = self._rules.match(
                filepath=str(path), timeout=self.timeout_seconds, fast=True
            )
        except Exception as exc:
            raise YaraScanError(f"YARA scan failed: {exc}") from exc

        matches = tuple(self._normalize_match(match) for match in raw_matches[:100])
        return YaraScanResult(
            status="completed", ruleset_version=self.ruleset_version, matches=matches
        )

    @staticmethod
    def _normalize_match(match: Any) -> YaraMatch:
        metadata = dict(getattr(match, "meta", {}) or {})
        raw_verdict = str(metadata.get("aegis_verdict", "")).strip().lower()
        verdict: YaraVerdict | None = (
            raw_verdict if raw_verdict in {"suspicious", "malicious"} else None
        )
        identifiers: list[str] = []
        for string_match in list(getattr(match, "strings", []) or [])[:32]:
            identifier = getattr(string_match, "identifier", None)
            if identifier and identifier not in identifiers:
                identifiers.append(str(identifier)[:100])

        def optional_text(key: str, limit: int = 500) -> str | None:
            value = metadata.get(key)
            return str(value)[:limit] if value not in (None, "") else None

        return YaraMatch(
            rule=str(match.rule)[:200],
            namespace=str(match.namespace)[:200],
            tags=tuple(str(tag)[:100] for tag in list(match.tags)[:30]),
            severity=optional_text("severity", 50),
            confidence=optional_text("confidence", 50),
            verdict=verdict,
            family=optional_text("family", 200),
            description=optional_text("description"),
            reference=optional_text("reference"),
            matched_strings=tuple(identifiers),
        )
