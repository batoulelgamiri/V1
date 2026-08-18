# User manual

## Start Aegis

Start the FastAPI backend from `backend/`, start Ollama if AI reports are wanted, then run the frontend from `frontend/`. Open `http://localhost:5173`. The top bar shows whether the detection engine is ready.

## Upload a file

1. Open **Manual analysis**.
2. Drag a file into the large intake area or choose **Select file**.
3. Confirm the name and size, then choose **Begin static analysis**.
4. Wait while the upload, static feature extraction, and classification complete.

Only genuine Windows PE files are supported. Changing a filename extension does not bypass validation.

## Understand results

- **Benign:** score is below the suspicious threshold. This is not proof that the file is safe.
- **Suspicious:** score reached the suspicious threshold but not the malicious threshold. Review evidence.
- **Malicious:** score reached the malicious threshold. Treat the file as a high-priority triage event.
- **Failed:** the model or an analysis dependency was unavailable. The reason appears on the detail page.

Configured thresholds are visible on **Settings**. The score is a model probability, not a severity percentage.

## View an analysis

Open a result after upload or choose one in **Analysis history**. The detail view shows hash, source, endpoint metadata, PE headers, section entropy, imports, classification, model version, and any cache relationship.

## AI report and PDF

Suspicious and malicious analyses request a local llama3 report. **Confirmed Evidence** contains static observations. **Suspected Behavior** contains inferences and must not be treated as verified runtime activity. If a validated report and PDF are available, choose **Download PDF**. Ollama/PDF failure does not remove the classifier result.

## Wazuh detections

Open **Wazuh detections** to see authenticated endpoint submissions. Filter by endpoint, filename, hash, path, or verdict. This view monitors detections; it cannot change Wazuh configuration.

## Common errors

- **Unsupported file type:** the content is not a parseable PE.
- **File exceeds limit:** the server rejected the stream before analysis.
- **Model setup required / unverified LIEF:** an administrator must complete the exact model setup.
- **AI analysis unavailable:** Ollama is offline or returned invalid structured data; classification remains usable.
- **PDF unavailable:** use the on-screen structured report and contact the administrator.
- **Wazuh authentication failed:** the endpoint API key does not match the server setting.

