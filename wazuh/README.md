# Wazuh endpoint forwarder

This adapter receives a detected path (directly or through a Wazuh alert JSON), verifies that the file still exists, checks the configured size ceiling and PE signature, then sends a multipart request to the authenticated central intake. It does not modify Wazuh configuration.

```powershell
python -m pip install -r requirements.txt
$env:AEGIS_API_URL = "https://aegis.example.internal"
$env:WAZUH_INGEST_API_KEY = "replace-with-a-long-random-secret"
python aegis_wazuh_forwarder.py --file "C:\\Samples\\suspect.exe"
```

For a Wazuh integration invocation, pass `--alert <alert-json-path>`. The adapter reads `syscheck.path` (or `data.path` as a fallback). Use TLS and a secret-management mechanism in production. Do not place the API key in command-line arguments where process listings may expose it.

