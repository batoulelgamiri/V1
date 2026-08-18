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
                         SQLite ← result ← XGBoost ← official EMBER v2 ← PE bytes
                                           │
                              suspicious or malicious
                                           ▼
                        evidence projection → Ollama → Pydantic schema
                                                    │
                                                    └─ reportlab PDF → protected storage
```

Every intake creates an event so Wazuh history is preserved. Cache lookup uses SHA-256 plus model version. A duplicate copies the stored technical result and references the canonical analysis; it does not rerun XGBoost, Ollama, or PDF generation.

## Boundaries

- **API:** HTTP contracts, authentication dependency, pagination, and safe error mapping.
- **Services:** analysis orchestration, upload streaming, hashing, and report coordination.
- **Analyzers:** PE validation/metadata and exact feature-vector construction.
- **Engine:** model loading, artifact verification, inference, and thresholds.
- **Integrations:** Ollama and Wazuh-specific contracts.
- **Repositories:** all ORM queries and persistence.
- **Reporting:** deterministic PDF layout from validated schema only.
- **Frontend:** typed-by-contract API access, workflow pages, state/error presentation, and device-local theme preference.

## Failure isolation

Invalid and oversized files never reach the model. Missing model dependencies create a stored failed analysis with a useful reason. Ollama and PDF failures update report status only. Central error handling hides tracebacks; structured logs keep event, analysis, source, classification, and status fields without secrets or file bytes.

## Evolution

A future engine can return the same `DetectionResult`; a future analyzer can sit beside the PE analyzer; PostgreSQL can replace SQLite behind repositories; workers can call the existing services; YARA or dynamic-analysis outputs can be added to `technical_data` and projected into the evidence context. No V1 module depends on Redis, Celery, Docker orchestration, or Wazuh configuration control.

