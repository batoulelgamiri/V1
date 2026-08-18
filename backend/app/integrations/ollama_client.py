from __future__ import annotations

import json
import logging
from typing import Any

import httpx
from pydantic import ValidationError

from app.schemas.report import StructuredReport


logger = logging.getLogger(__name__)


class ReportGenerationError(RuntimeError):
    pass


def parse_structured_report(raw: str) -> StructuredReport:
    text = raw.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    try:
        return StructuredReport.model_validate_json(text)
    except (ValidationError, json.JSONDecodeError) as exc:
        start, end = text.find("{"), text.rfind("}")
        if start >= 0 and end > start:
            try:
                return StructuredReport.model_validate_json(text[start : end + 1])
            except (ValidationError, json.JSONDecodeError):
                pass
        raise ReportGenerationError(f"Ollama returned invalid structured JSON: {exc}") from exc


class OllamaClient:
    def __init__(self, base_url: str, model: str, timeout_seconds: float) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout_seconds = timeout_seconds

    def generate_report(self, evidence: dict[str, Any]) -> StructuredReport:
        prompt = self._build_prompt(evidence)
        first_response = self._request(prompt)
        try:
            return parse_structured_report(first_response)
        except ReportGenerationError as first_error:
            repair_prompt = (
                "Repair the following response into JSON that exactly matches the required schema. "
                "Preserve only claims supported by the confirmed evidence. Return JSON only.\n\n"
                f"Invalid response:\n{first_response[:12000]}\n\n"
                f"Validation problem:\n{first_error}"
            )
            repaired_response = self._request(repair_prompt)
            return parse_structured_report(repaired_response)

    def _request(self, prompt: str) -> str:
        try:
            with httpx.Client(timeout=self.timeout_seconds) as client:
                response = client.post(
                    f"{self.base_url}/api/generate",
                    json={
                        "model": self.model,
                        "prompt": prompt,
                        "stream": False,
                        "format": StructuredReport.model_json_schema(),
                        "options": {"temperature": 0.1},
                    },
                )
                response.raise_for_status()
                payload = response.json()
        except (httpx.HTTPError, json.JSONDecodeError, ValueError) as exc:
            raise ReportGenerationError(f"Ollama request failed: {exc}") from exc
        text = payload.get("response")
        if not isinstance(text, str) or not text.strip():
            raise ReportGenerationError("Ollama returned an empty response.")
        return text

    @staticmethod
    def _build_prompt(evidence: dict[str, Any]) -> str:
        schema = json.dumps(StructuredReport.model_json_schema(), indent=2)
        confirmed = json.dumps(evidence, indent=2, ensure_ascii=False)
        return f"""You are a malware triage analyst producing a static-analysis report.

Rules:
- The JSON under CONFIRMED EVIDENCE is the complete factual record. Do not invent evidence.
- Clearly separate confirmed technical indicators from suspected capabilities.
- A suspected capability is an inference, never a confirmed runtime behavior.
- Include MITRE ATT&CK mappings only when the evidence supports them; otherwise use an empty list.
- Mention that static analysis cannot confirm runtime behavior.
- Return JSON only, matching the schema exactly.

CONFIRMED EVIDENCE:
{confirmed}

REQUIRED JSON SCHEMA:
{schema}
"""

