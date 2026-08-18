# Module guide

## Upload validation — `services/upload_service.py`

- **Purpose:** stream multipart data into a server-named temporary file with an enforced ceiling.
- **Input/output:** `UploadFile` → temporary path, byte count, sanitized display name.
- **Dependencies:** filesystem and FastAPI upload abstraction.
- **Failure:** removes partial data and raises a clear validation error.
- **Extend:** add content-independent policies here; keep PE-specific validation in the analyzer.

## PE parser — `analyzers/pe_parser.py`

- **Purpose:** verify DOS/PE signatures, require `pefile` parsing, and collect static metadata.
- **Input/output:** bounded local file → JSON-safe architecture, headers, sections, entropy, imports, exports, and printable strings.
- **Dependencies:** `pefile`; it is not the model feature extractor.
- **Failure:** unsupported content stops before inference.
- **Extend:** add reliable static indicators without changing EMBER ordering.

## Feature extraction — `analyzers/feature_extractor.py`

- **Purpose:** invoke official `PEFeatureExtractor(feature_version=2)` and enforce the 2,381-value contract.
- **Input/output:** PE bytes → finite NumPy float32 vector.
- **Dependencies:** pinned Elastic EMBER and verified LIEF 0.9.0/0.10.1.
- **Failure:** raises unavailable instead of approximating features.
- **Extend:** create a separate versioned adapter for another model/pipeline.

## XGBoost engine — `engines/xgboost_engine.py`

- **Purpose:** verify artifact hash/count, load once, infer probability, and apply centralized thresholds.
- **Input/output:** PE path → `DetectionResult`.
- **Dependencies:** exact feature adapter, NumPy, XGBoost.
- **Failure:** returns a model-unavailable condition to the orchestration service.
- **Extend:** implement another small adapter returning the same result shape.

## Analysis service — `services/analysis_service.py`

- **Purpose:** coordinate validation, hashing, cache, metadata, inference, persistence, and optional reporting.
- **Input/output:** intake file plus trusted source fields → stored `Analysis`.
- **Dependencies:** repositories, analyzers, engine, report service.
- **Failure:** stores expected inference failures and logs unexpected failures.
- **Extend:** call additional engines after PE parsing and store a versioned unified result.

## Wazuh ingestion — `api/routes/analyses.py`, `wazuh/aegis_wazuh_forwarder.py`

- **Purpose:** authenticate central intake and safely forward endpoint-detected files.
- **Input/output:** multipart file plus endpoint metadata → normal analysis result.
- **Dependencies:** constant-time API-key comparison and HTTP client.
- **Failure:** 401 before file processing; endpoint adapter validates existence, size, and PE signature.
- **Extend:** replace API key dependency with mTLS or signed endpoint identity.

## Ollama client — `integrations/ollama_client.py`

- **Purpose:** send static evidence only and validate structured llama3 output.
- **Input/output:** JSON evidence → `StructuredReport`.
- **Dependencies:** `httpx`, Ollama, Pydantic.
- **Failure:** retries once with a repair prompt, then records a report error.
- **Extend:** add another provider behind the same validated-report return value.

## Report service — `services/report_service.py`

- **Purpose:** project stored technical data into confirmed evidence, request enrichment, persist JSON, and request PDF.
- **Input/output:** completed threat analysis → report record.
- **Dependencies:** Ollama client, report repository, PDF generator.
- **Failure:** classifier result remains unchanged; structured output survives PDF failure.
- **Extend:** add report regeneration or version fields without placing logic in routes.

## PDF generator — `reporting/pdf_generator.py`

- **Purpose:** render consistent analyst PDFs from validated models.
- **Input/output:** `Analysis` + `StructuredReport` → protected PDF path.
- **Dependencies:** reportlab only.
- **Failure:** removes partial output and raises a scoped error.
- **Extend:** change templates or add branding without touching API code.

## Database repositories — `repositories/`

- **Purpose:** isolate SQLAlchemy queries for analyses, reports, and endpoints.
- **Input/output:** domain/filters → ORM entities and aggregates.
- **Dependencies:** SQLAlchemy session.
- **Failure:** bubbles database errors to central logging/error handling.
- **Extend:** preserve repository method contracts when moving to PostgreSQL.

