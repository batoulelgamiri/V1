from fastapi.testclient import TestClient
import pytest
from pydantic import ValidationError

from app.core.config import Settings
from app.main import app


def test_wazuh_ingest_requires_api_key() -> None:
    with TestClient(app) as client:
        response = client.post(
            "/api/analyses/wazuh",
            data={
                "endpoint_id": "endpoint-01",
                "endpoint_name": "LAB-01",
                "file_path": r"C:\\sample.exe",
            },
            files={"file": ("sample.exe", b"not-pe", "application/octet-stream")},
        )
    assert response.status_code == 401
    assert "API key" in response.json()["detail"]


def test_wazuh_ingest_rejects_wrong_api_key() -> None:
    with TestClient(app) as client:
        response = client.post(
            "/api/analyses/wazuh",
            headers={"X-API-Key": "wrong"},
            data={
                "endpoint_id": "endpoint-01",
                "endpoint_name": "LAB-01",
                "file_path": r"C:\\sample.exe",
            },
            files={"file": ("sample.exe", b"not-pe", "application/octet-stream")},
        )
    assert response.status_code == 401


def test_default_wazuh_key_is_forbidden_in_production() -> None:
    with pytest.raises(ValidationError, match="must be changed"):
        Settings(app_env="production", wazuh_ingest_api_key="change-me")
