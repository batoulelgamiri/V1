from __future__ import annotations

import math
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pefile


class UnsupportedFileError(ValueError):
    pass


MACHINE_TYPES = {
    0x014C: "x86",
    0x0200: "Itanium",
    0x8664: "x86-64",
    0x01C0: "ARM",
    0xAA64: "ARM64",
}


def validate_pe(path: Path) -> None:
    with path.open("rb") as handle:
        dos = handle.read(64)
        if len(dos) < 64 or dos[:2] != b"MZ":
            raise UnsupportedFileError(
                "Unsupported file type. This version currently supports Windows Portable Executable files."
            )
        pe_offset = int.from_bytes(dos[0x3C:0x40], "little")
        if pe_offset < 64 or pe_offset > path.stat().st_size - 4:
            raise UnsupportedFileError(
                "Unsupported file type. This version currently supports Windows Portable Executable files."
            )
        handle.seek(pe_offset)
        if handle.read(4) != b"PE\x00\x00":
            raise UnsupportedFileError(
                "Unsupported file type. This version currently supports Windows Portable Executable files."
            )
    pe: pefile.PE | None = None
    try:
        pe = pefile.PE(str(path), fast_load=True)
    except pefile.PEFormatError as exc:
        raise UnsupportedFileError(
            "Unsupported file type. This version currently supports Windows Portable Executable files."
        ) from exc
    finally:
        if pe is not None:
            pe.close()


def _entropy(data: bytes) -> float:
    if not data:
        return 0.0
    counts = [0] * 256
    for value in data:
        counts[value] += 1
    size = len(data)
    return -sum((count / size) * math.log2(count / size) for count in counts if count)


def parse_pe(path: Path) -> dict[str, Any]:
    pe = pefile.PE(str(path), fast_load=False)
    try:
        sections = []
        for section in pe.sections[:32]:
            name = section.Name.rstrip(b"\x00").decode("utf-8", errors="replace") or "<unnamed>"
            sections.append(
                {
                    "name": name,
                    "virtual_size": int(section.Misc_VirtualSize),
                    "raw_size": int(section.SizeOfRawData),
                    "entropy": round(float(section.get_entropy()), 3),
                    "characteristics": f"0x{section.Characteristics:08x}",
                }
            )

        imports: list[dict[str, Any]] = []
        for entry in getattr(pe, "DIRECTORY_ENTRY_IMPORT", [])[:80]:
            library = entry.dll.decode("utf-8", errors="replace")
            symbols = []
            for item in entry.imports[:100]:
                symbols.append(
                    item.name.decode("utf-8", errors="replace")
                    if item.name
                    else f"ordinal:{item.ordinal}"
                )
            imports.append({"library": library, "symbols": symbols})

        exports: list[str] = []
        export_directory = getattr(pe, "DIRECTORY_ENTRY_EXPORT", None)
        if export_directory:
            exports = [
                symbol.name.decode("utf-8", errors="replace")
                if symbol.name
                else f"ordinal:{symbol.ordinal}"
                for symbol in export_directory.symbols[:200]
            ]

        bytez = path.read_bytes()
        printable = re.findall(rb"[ -~]{6,}", bytez)
        strings = [value[:240].decode("utf-8", errors="replace") for value in printable[:120]]

        timestamp = int(pe.FILE_HEADER.TimeDateStamp)
        try:
            compiled_at = (
                datetime.fromtimestamp(timestamp, timezone.utc).isoformat() if timestamp else None
            )
        except (ValueError, OSError, OverflowError):
            compiled_at = None

        optional = pe.OPTIONAL_HEADER
        return {
            "architecture": MACHINE_TYPES.get(pe.FILE_HEADER.Machine, f"0x{pe.FILE_HEADER.Machine:04x}"),
            "machine": f"0x{pe.FILE_HEADER.Machine:04x}",
            "compiled_at": compiled_at,
            "entry_point": f"0x{optional.AddressOfEntryPoint:x}",
            "image_base": f"0x{optional.ImageBase:x}",
            "subsystem": int(optional.Subsystem),
            "number_of_sections": int(pe.FILE_HEADER.NumberOfSections),
            "characteristics": f"0x{pe.FILE_HEADER.Characteristics:04x}",
            "overall_entropy": round(_entropy(bytez), 3),
            "sections": sections,
            "imports": imports,
            "exports": exports,
            "strings": strings,
            "strings_truncated": len(printable) > len(strings),
        }
    finally:
        pe.close()
