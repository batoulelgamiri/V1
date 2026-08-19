from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


BACKEND_DIR = Path(__file__).resolve().parents[2]
PROJECT_DIR = BACKEND_DIR.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(PROJECT_DIR / ".env", BACKEND_DIR / ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "Aegis PE Intelligence"
    app_env: str = "development"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    log_level: str = "INFO"

    database_url: str = "sqlite:///./data/app.db"
    storage_dir: Path = Path("./storage")
    model_dir: Path = Path("./models")
    model_filename: str = "baseline_xgboost.json"
    model_expected_sha256: str = (
        "1dafb3b9c826457c158f8950687ad653f005dd4d5a29a39040047499405e08ee"
    )
    max_file_size_mb: int = Field(default=100, ge=1, le=2048)

    suspicious_threshold: float = Field(default=0.50, ge=0.0, le=1.0)
    malicious_threshold: float = Field(default=0.80, ge=0.0, le=1.0)

    yara_enabled: bool = True
    yara_rules_dir: Path = Path("./rules")
    yara_timeout_seconds: int = Field(default=10, ge=1, le=120)

    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3"
    ollama_timeout_seconds: float = Field(default=120, gt=0)

    wazuh_ingest_api_key: str = "change-me"
    cors_origins: str = "http://localhost:5173"

    @model_validator(mode="after")
    def validate_thresholds(self) -> "Settings":
        if self.suspicious_threshold >= self.malicious_threshold:
            raise ValueError("SUSPICIOUS_THRESHOLD must be lower than MALICIOUS_THRESHOLD")
        if self.app_env.lower() == "production" and self.wazuh_ingest_api_key == "change-me":
            raise ValueError("WAZUH_INGEST_API_KEY must be changed before production startup")
        return self

    @field_validator("model_expected_sha256")
    @classmethod
    def validate_sha256(cls, value: str) -> str:
        normalized = value.strip().lower()
        if normalized and (len(normalized) != 64 or any(c not in "0123456789abcdef" for c in normalized)):
            raise ValueError("MODEL_EXPECTED_SHA256 must be a 64-character hexadecimal digest")
        return normalized

    @property
    def max_file_size_bytes(self) -> int:
        return self.max_file_size_mb * 1024 * 1024

    @property
    def model_path(self) -> Path:
        return self.resolve_path(self.model_dir) / self.model_filename

    @property
    def resolved_storage_dir(self) -> Path:
        return self.resolve_path(self.storage_dir)

    @property
    def resolved_yara_rules_dir(self) -> Path:
        return self.resolve_path(self.yara_rules_dir)

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @staticmethod
    def resolve_path(path: Path) -> Path:
        return path if path.is_absolute() else (BACKEND_DIR / path).resolve()


@lru_cache
def get_settings() -> Settings:
    return Settings()
