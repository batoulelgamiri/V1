# Aegis PE Intelligence

Aegis is a modular-monolith malware triage platform for Windows Portable Executables. It streams and validates untrusted uploads, deduplicates samples by SHA-256 and model version, extracts the exact EMBER 2018 v2 representation required by X-MalForensics-XGBoost, stores results in SQLite, and enriches suspicious or malicious verdicts through local Ollama/llama3. It performs static analysis only—never execution or remediation.

## What is included

- FastAPI backend with isolated routes, services, analyzers, repositories, and reporting modules
- React + Vite + Tailwind dashboard with six responsive views and intentional dark/light themes
- Manual drag-and-drop PE analysis and authenticated Wazuh multipart intake
- Streaming 100 MB default upload ceiling, real PE-header/structure validation, SHA-256 caching
- Layered YARA signature evidence plus XGBoost probability and deterministic verdict fusion
- Structured, Pydantic-validated Ollama reports and reportlab PDF generation
- SQLite history, dashboard metrics, endpoint registry, filtering, pagination, and safe error states
- Endpoint forwarder, unit/integration tests, model setup verification, and operator documentation

## Architecture

```text
React/Vite dashboard
        │ REST / multipart
        ▼
FastAPI routes ── repositories ── SQLite
        │
        ├─ upload guard → PE validator → SHA-256 cache
        │                         │
        │                         ▼
        │                PE parser + EMBER v2
        │                         │
        │                         ▼
        │       YARA rules + XGBoost model adapter
        │                         │
        │       suspicious/malicious only
        │                         ▼
        └──────────── Ollama/llama3 → schema validation → PDF
```

YARA evidence and the XGBoost probability remain individually visible while a deterministic service produces the final verdict. Ollama and PDF failures are isolated and never erase those results. See [Architecture](docs/ARCHITECTURE.md) and [Module guide](docs/MODULES.md).

## Requirements

- Conda with Python 3.10 (recommended for the exact historical LIEF build)
- Node.js 20+ and npm
- Ollama with `llama3` for AI reports (optional for benign/core classification)
- The public model artifact installed by the provided setup script

## 1. Configure

Copy `.env.example` to `.env` and change at least `WAZUH_INGEST_API_KEY` to a long random value. Paths in the defaults are resolved from `backend/` when the server is started there.

Threshold interpretation is explicit:

- `score < SUSPICIOUS_THRESHOLD`: benign
- `SUSPICIOUS_THRESHOLD <= score < MALICIOUS_THRESHOLD`: suspicious
- `score >= MALICIOUS_THRESHOLD`: malicious

YARA is enabled by default with reviewed rules in `backend/rules/`. Rules are compiled once at startup, scanned with a timeout, and fingerprinted into the analysis cache version. Only rules that explicitly set `aegis_verdict = "suspicious"` or `aegis_verdict = "malicious"` may override the model-only classification; all other matches remain informational evidence. Restart the backend after changing rules.

## 2. Install the backend and exact model pipeline

The model is not committed. Follow [Model setup](docs/MODEL_SETUP.md); the short form is:

```powershell
conda env create -f environment.yml
conda activate aegis-pe
python backend/scripts/setup_model.py
```

Start from the backend directory so the default SQLite and storage paths remain local to it:

```powershell
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

OpenAPI is at `http://localhost:8000/docs`; health is at `http://localhost:8000/api/health`.

## 3. Start Ollama

```powershell
ollama pull llama3
ollama serve
```

Defaults are `OLLAMA_BASE_URL=http://localhost:11434` and `OLLAMA_MODEL=llama3`. If Ollama is offline, suspicious/malicious classification still completes and the analysis detail reports that enrichment is unavailable.

## 4. Install and run the frontend

```powershell
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`. Vite proxies `/api` to the backend during development. For another API origin, set `VITE_API_BASE_URL` when building.

## Manual analysis

Open **Manual analysis**, drop a PE file, and choose **Begin static analysis**. A repeated SHA-256/model-version combination creates a new intake event referencing the cached canonical result; XGBoost, Ollama, and PDF generation are not rerun. This preserves Wazuh/manual event history while avoiding expensive duplicate work.

## Wazuh intake

The dashboard never edits Wazuh configuration. Install the standalone dependencies in `wazuh/requirements.txt`, configure `AEGIS_API_URL`, `WAZUH_INGEST_API_KEY`, and endpoint identity, then invoke [the forwarder](wazuh/aegis_wazuh_forwarder.py) with either a detected file or an alert JSON. Full instructions are in [wazuh/README.md](wazuh/README.md).

Example central request:

```powershell
curl.exe -X POST http://localhost:8000/api/analyses/wazuh `
  -H "X-API-Key: change-me" `
  -F "endpoint_id=endpoint-01" `
  -F "endpoint_name=WORKSTATION-01" `
  -F "file_path=C:\\Samples\\file.exe" `
  -F "file=@C:\\Samples\\file.exe"
```

Use HTTPS between endpoints and the central API in production.

## Tests and builds

```powershell
cd backend
python -m pip install -r requirements-dev.txt
pytest

cd ../frontend
npm run build
```

Tests mock external inference where appropriate and do not need live Ollama or Wazuh. The model adapter itself refuses unverified preprocessing rather than substituting fabricated features.

## Troubleshooting

- **Model setup required:** run `backend/scripts/setup_model.py`, install the exact pipeline, and confirm `/api/health` reports `model_available: true`.
- **LIEF version not verified:** use the Conda `py-lief=0.10.1` environment. Newer LIEF may parse files but is intentionally rejected because feature drift is possible.
- **YARA unavailable:** install `backend/requirements.txt`, verify that `backend/rules/` contains valid `.yar` files, and restart the backend. Health exposes YARA status separately from the model.
- **Unsupported file type:** extension is irrelevant; the file must contain a valid PE signature and parse as a PE.
- **File exceeds limit:** raise `MAX_FILE_SIZE_MB` only after considering memory use; EMBER extraction ultimately requires the bounded file bytes.
- **AI report unavailable:** verify `ollama serve`, `ollama list`, the configured URL/model, and backend logs.
- **PDF unavailable:** the validated structured report stays readable; check storage permissions and backend logs.
- **Wazuh 401:** endpoint and central `WAZUH_INGEST_API_KEY` values must match exactly.

## Security notes

Uploads receive server-generated temporary names, are not exposed as static files, are never executed, and are removed after analysis. API keys, raw executables, and complete file contents are not logged. SQLite and generated PDFs belong in protected server storage. This V1 has no automatic deletion, quarantine, blocking, process termination, or Wazuh configuration management.
