from __future__ import annotations

import os
import struct
from pathlib import Path

import pytest


TEST_DATABASE = Path(__file__).resolve().parent / "test-app.db"
os.environ.setdefault("DATABASE_URL", f"sqlite:///{TEST_DATABASE.as_posix()}")
os.environ.setdefault("WAZUH_INGEST_API_KEY", "unit-test-key")


def build_minimal_pe() -> bytes:
    dos = bytearray(0x80)
    dos[:2] = b"MZ"
    struct.pack_into("<I", dos, 0x3C, 0x80)
    file_header = struct.pack("<HHIIIHH", 0x14C, 1, 0, 0, 0, 0xE0, 0x010F)
    optional = bytearray(0xE0)
    struct.pack_into("<H", optional, 0, 0x10B)
    struct.pack_into("<I", optional, 16, 0x1000)
    struct.pack_into("<I", optional, 20, 0x1000)
    struct.pack_into("<I", optional, 24, 0x2000)
    struct.pack_into("<I", optional, 28, 0x400000)
    struct.pack_into("<I", optional, 32, 0x1000)
    struct.pack_into("<I", optional, 36, 0x200)
    struct.pack_into("<I", optional, 56, 0x2000)
    struct.pack_into("<I", optional, 60, 0x200)
    struct.pack_into("<H", optional, 68, 3)
    struct.pack_into("<I", optional, 92, 16)
    section = bytearray(40)
    section[:8] = b".text\x00\x00\x00"
    struct.pack_into("<I", section, 8, 0x10)
    struct.pack_into("<I", section, 12, 0x1000)
    struct.pack_into("<I", section, 16, 0x200)
    struct.pack_into("<I", section, 20, 0x200)
    struct.pack_into("<I", section, 36, 0x60000020)
    headers = bytes(dos) + b"PE\x00\x00" + file_header + bytes(optional) + bytes(section)
    headers += b"\x00" * (0x200 - len(headers))
    return headers + b"\xC3" + b"\x00" * 0x1FF


@pytest.fixture
def minimal_pe(tmp_path: Path) -> Path:
    path = tmp_path / "sample.exe"
    path.write_bytes(build_minimal_pe())
    return path


@pytest.fixture(scope="session", autouse=True)
def remove_test_database():
    yield
    from app.database.session import engine

    engine.dispose()
    TEST_DATABASE.unlink(missing_ok=True)
