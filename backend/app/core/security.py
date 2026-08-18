from __future__ import annotations

import secrets


def api_keys_match(provided: str | None, configured: str) -> bool:
    if not provided or not configured:
        return False
    return secrets.compare_digest(provided.encode("utf-8"), configured.encode("utf-8"))

