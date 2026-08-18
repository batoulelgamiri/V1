from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile


class UploadValidationError(ValueError):
    pass


async def save_upload_limited(
    upload: UploadFile,
    destination_dir: Path,
    max_bytes: int,
    chunk_size: int = 1024 * 1024,
) -> tuple[Path, int, str]:
    destination_dir.mkdir(parents=True, exist_ok=True)
    safe_original_name = Path(upload.filename or "unnamed.pe").name[:255]
    destination = destination_dir / f"{uuid4().hex}.upload"
    total = 0
    try:
        with destination.open("xb") as handle:
            while chunk := await upload.read(chunk_size):
                total += len(chunk)
                if total > max_bytes:
                    raise UploadValidationError(
                        f"File exceeds the configured {max_bytes // (1024 * 1024)} MB limit."
                    )
                handle.write(chunk)
        if total == 0:
            raise UploadValidationError("The uploaded file is empty.")
        return destination, total, safe_original_name
    except Exception:
        destination.unlink(missing_ok=True)
        raise
    finally:
        await upload.close()

