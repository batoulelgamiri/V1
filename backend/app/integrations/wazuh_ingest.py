from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class WazuhIngestMetadata:
    endpoint_id: str
    endpoint_name: str
    file_path: str

    def sanitized(self) -> "WazuhIngestMetadata":
        return WazuhIngestMetadata(
            endpoint_id=self.endpoint_id.strip()[:255],
            endpoint_name=self.endpoint_name.strip()[:255],
            file_path=self.file_path.strip()[:2048],
        )

