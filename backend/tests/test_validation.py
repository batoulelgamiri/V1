from __future__ import annotations

import asyncio
from io import BytesIO
from pathlib import Path

import pytest
from fastapi import UploadFile

from app.analyzers.pe_parser import UnsupportedFileError, parse_pe, validate_pe
from app.services.hash_service import sha256_file
from app.services.upload_service import UploadValidationError, save_upload_limited


def test_valid_pe_is_accepted(minimal_pe: Path) -> None:
    validate_pe(minimal_pe)
    parsed = parse_pe(minimal_pe)
    assert parsed["architecture"] == "x86"
    assert parsed["sections"][0]["name"] == ".text"


def test_pe_parser_releases_file_handle(minimal_pe: Path) -> None:
    validate_pe(minimal_pe)
    parse_pe(minimal_pe)
    minimal_pe.unlink()
    assert not minimal_pe.exists()


def test_invalid_file_is_rejected(tmp_path: Path) -> None:
    path = tmp_path / "fake.exe"
    path.write_bytes(b"not a portable executable")
    with pytest.raises(UnsupportedFileError, match="Portable Executable"):
        validate_pe(path)


def test_hash_is_streamed(tmp_path: Path) -> None:
    path = tmp_path / "value.bin"
    path.write_bytes(b"aegis")
    assert sha256_file(path) == "598f7a741a1e3a05654d346033571fda567af6dc2bf099b34b930171519d995f"


def test_upload_size_limit_removes_partial_file(tmp_path: Path) -> None:
    upload = UploadFile(filename="large.exe", file=BytesIO(b"x" * 12))
    with pytest.raises(UploadValidationError, match="configured"):
        asyncio.run(save_upload_limited(upload, tmp_path, max_bytes=10, chunk_size=4))
    assert list(tmp_path.iterdir()) == []
