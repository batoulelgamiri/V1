"""Forward a Wazuh-detected PE to the central Aegis intake API.

This adapter does not modify Wazuh configuration and never executes the file.
It can be called directly with --file or receive a Wazuh alert JSON path whose
``syscheck.path`` field identifies the changed file.
"""

from __future__ import annotations

import argparse
import json
import os
import socket
import sys
from pathlib import Path
from typing import Any

import httpx


def valid_pe_header(path: Path) -> bool:
    with path.open("rb") as handle:
        dos = handle.read(64)
        if len(dos) < 64 or dos[:2] != b"MZ":
            return False
        pe_offset = int.from_bytes(dos[0x3C:0x40], "little")
        if pe_offset < 64 or pe_offset > path.stat().st_size - 4:
            return False
        handle.seek(pe_offset)
        return handle.read(4) == b"PE\x00\x00"


def nested(mapping: dict[str, Any], *keys: str) -> Any:
    value: Any = mapping
    for key in keys:
        if not isinstance(value, dict):
            return None
        value = value.get(key)
    return value


def file_from_alert(alert_path: Path) -> Path:
    payload = json.loads(alert_path.read_text(encoding="utf-8"))
    detected = nested(payload, "syscheck", "path") or nested(payload, "data", "path")
    if not isinstance(detected, str) or not detected:
        raise ValueError("Alert does not contain syscheck.path or data.path.")
    return Path(detected)


def forward(
    *,
    path: Path,
    api_url: str,
    api_key: str,
    endpoint_id: str,
    endpoint_name: str,
    max_bytes: int,
) -> dict[str, Any]:
    resolved = path.resolve(strict=True)
    if not resolved.is_file():
        raise ValueError("Detected path is not a regular file.")
    size = resolved.stat().st_size
    if size <= 0 or size > max_bytes:
        raise ValueError(f"File size is outside the allowed range (1..{max_bytes} bytes).")
    if not valid_pe_header(resolved):
        raise ValueError("Detected file is not a Windows Portable Executable.")

    with resolved.open("rb") as handle, httpx.Client(timeout=180) as client:
        response = client.post(
            f"{api_url.rstrip('/')}/api/analyses/wazuh",
            headers={"X-API-Key": api_key},
            data={
                "endpoint_id": endpoint_id[:255],
                "endpoint_name": endpoint_name[:255],
                "file_path": str(path)[:2048],
            },
            files={"file": (resolved.name, handle, "application/octet-stream")},
        )
        response.raise_for_status()
        return response.json()


def main() -> int:
    parser = argparse.ArgumentParser(description="Forward a detected PE to Aegis")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--file", type=Path, help="Detected file path")
    source.add_argument("--alert", type=Path, help="Wazuh alert JSON path")
    parser.add_argument("--api-url", default=os.getenv("AEGIS_API_URL", "http://127.0.0.1:8000"))
    parser.add_argument("--api-key", default=os.getenv("WAZUH_INGEST_API_KEY"))
    parser.add_argument("--endpoint-id", default=os.getenv("WAZUH_ENDPOINT_ID", socket.gethostname()))
    parser.add_argument("--endpoint-name", default=os.getenv("WAZUH_ENDPOINT_NAME", socket.gethostname()))
    parser.add_argument("--max-mb", type=int, default=int(os.getenv("MAX_FILE_SIZE_MB", "100")))
    args = parser.parse_args()
    if not args.api_key:
        print("WAZUH_INGEST_API_KEY is required.", file=sys.stderr)
        return 2

    try:
        path = args.file or file_from_alert(args.alert)
        result = forward(
            path=path,
            api_url=args.api_url,
            api_key=args.api_key,
            endpoint_id=args.endpoint_id,
            endpoint_name=args.endpoint_name,
            max_bytes=args.max_mb * 1024 * 1024,
        )
    except (OSError, ValueError, json.JSONDecodeError, httpx.HTTPError) as exc:
        print(f"Aegis forward failed: {exc}", file=sys.stderr)
        return 1
    print(json.dumps({"analysis_id": result.get("id"), "status": result.get("status")}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

