# Architecture

## Why a modular monolith

Aegis runs as one FastAPI process plus one React client. Upload coordination, static parsing, inference, reporting, and persistence stay deployable together while module boundaries prevent route, model, database, and LLM concerns from becoming tangled. V1 needs neither queues nor distributed consistency; those would add failure modes without improving the required workflow.

## Data flow

```text
manual browser upload ─┐
                      ├─ bounded multipart stream → PE validation → SHA-256
Wazuh + API key ──────┘                                  │
                                                        ├─ cache hit → new event references stored result
                                                        │
                                                        └─ cache miss
                                                             │
                         SQLite ← combined verdict ←┬─ XGBoost ← official EMBER v2 ← PE bytes
                                                    └─ YARA ruleset ← PE bytes
                                           │
                              suspicious or malicious
                                           ▼
                        evidence projection → Ollama → Pydantic schema
                                                    │
                                                    └─ reportlab PDF → protected storage
```

Every intake creates an event so Wazuh history is preserved. Cache lookup uses SHA-256 plus the XGBoost model and YARA ruleset versions. A rule change therefore cannot reuse a stale verdict. A duplicate copies the stored technical result and references the canonical analysis; it does not rerun YARA, XGBoost, Ollama, or PDF generation.

## Boundaries

- **API:** HTTP contracts, authentication dependency, pagination, and safe error mapping.
- **Services:** analysis orchestration, upload streaming, hashing, and report coordination.
- **Analyzers:** PE validation/metadata and exact feature-vector construction.
- **Engines:** model loading, artifact verification, YARA compilation/scanning, inference, and thresholds.
- **Integrations:** Ollama and Wazuh-specific contracts.
- **Repositories:** all ORM queries and persistence.
- **Reporting:** deterministic PDF layout from validated schema only.
- **Frontend:** typed-by-contract API access, workflow pages, state/error presentation, and device-local theme preference.

## Failure isolation

Invalid and oversized files never reach the engines. Missing model dependencies create a stored failed analysis with a useful reason. A missing or invalid YARA layer is recorded as partial evidence without silently changing the XGBoost result. Ollama and PDF failures update report status only. Central error handling hides tracebacks; structured logs keep event, analysis, source, classification, and status fields without secrets or file bytes.

## Evolution

A future engine can return its own evidence contract; a future analyzer can sit beside the PE analyzer; PostgreSQL can replace SQLite behind repositories; workers can call the existing services; dynamic-analysis outputs can be added to `technical_data` and projected into the evidence context. No V1 module depends on Redis, Celery, Docker orchestration, or Wazuh configuration control.
