"""Read-only installer file/EFI checks; no partition or hardware boot claims."""

from __future__ import annotations

import importlib.util
import argparse
import json
import os
from pathlib import Path
import struct

_spec = importlib.util.spec_from_file_location(
    "_readback_workspace", Path(__file__).with_name("prepare_windows_workspace.py")
)
workspace = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(workspace)
media = workspace.preparation.media

EFI_TARGETS = {
    "x64": ("bootx64.efi", 0x8664, 0x20B),
    "arm64": ("bootaa64.efi", 0xAA64, 0x20B),
    "x86": ("bootia32.efi", 0x14C, 0x10B),
}


def inspect_efi_application(path: Path, architecture: str) -> dict:
    """Bounded PE-header inspection, without executing or trusting the binary."""
    if architecture not in EFI_TARGETS:
        raise ValueError("Explicit x64, arm64 or x86 architecture is required")
    _, expected_machine, expected_magic = EFI_TARGETS[architecture]
    with workspace._open_regular(path) as stream:
        before = os.fstat(stream.fileno())
        dos = stream.read(64)
        if len(dos) != 64 or dos[:2] != b"MZ":
            raise ValueError("EFI loader lacks a DOS/PE header")
        offset = struct.unpack_from("<I", dos, 60)[0]
        if offset < 64 or offset > min(before.st_size - 24, 1024 * 1024):
            raise ValueError(
                "EFI PE-header offset is invalid or exceeds inspection limit"
            )
        stream.seek(offset)
        header = stream.read(24)
        if len(header) != 24 or header[:4] != b"PE\0\0":
            raise ValueError("EFI loader PE signature is invalid")
        machine, sections = struct.unpack_from("<HH", header, 4)
        optional_size, characteristics = struct.unpack_from("<HH", header, 20)
        minimum = 112 if expected_magic == 0x20B else 96
        if machine != expected_machine:
            raise ValueError("EFI loader architecture mismatch")
        if (
            not 1 <= sections <= 96
            or not characteristics & 2
            or characteristics & 0x2000
        ):
            raise ValueError("EFI loader must be an executable image, not a DLL")
        if (
            optional_size < minimum
            or offset + 24 + optional_size + sections * 40 > before.st_size
        ):
            raise ValueError("EFI optional header or section table is truncated")
        optional = stream.read(optional_size)
        magic = struct.unpack_from("<H", optional)[0]
        subsystem = struct.unpack_from("<H", optional, 68)[0]
        entrypoint = struct.unpack_from("<I", optional, 16)[0]
        image_size = struct.unpack_from("<I", optional, 56)[0]
        headers_size = struct.unpack_from("<I", optional, 60)[0]
        table_end = offset + 24 + optional_size + sections * 40
        if (
            magic != expected_magic
            or subsystem != 10
            or not 0 < entrypoint < image_size
            or not table_end <= headers_size <= min(before.st_size, image_size)
        ):
            raise ValueError("EFI optional header is not a matching EFI application")
        # Ensure every section's raw bytes exist and the entry point maps to
        # executable file-backed bytes. This is structural proof, not trust.
        entry_mapped = False
        virtual_ranges, raw_ranges = [], []
        for _ in range(sections):
            section = stream.read(40)
            virtual_size, address, raw_size, raw_offset = struct.unpack_from(
                "<IIII", section, 8
            )
            flags = struct.unpack_from("<I", section, 36)[0]
            extent = max(virtual_size, raw_size)
            if not extent or address < headers_size or address + extent > image_size:
                raise ValueError("EFI section virtual extent is outside the image")
            virtual_ranges.append((address, address + extent))
            if raw_size and (
                raw_offset < headers_size or raw_offset + raw_size > before.st_size
            ):
                raise ValueError("EFI section points outside the loader file")
            if raw_size:
                raw_ranges.append((raw_offset, raw_offset + raw_size))
            delta = entrypoint - address
            if 0 <= delta < min(virtual_size, raw_size) and flags & 0x20000000:
                entry_mapped = True
        for ranges in (virtual_ranges, raw_ranges):
            ranges.sort()
            if any(a[1] > b[0] for a, b in zip(ranges, ranges[1:])):
                raise ValueError("EFI section ranges overlap")
        if not entry_mapped:
            raise ValueError("EFI entry point is not backed by executable file bytes")
        after = os.fstat(stream.fileno())
        if media.file_stat_identity(before) != media.file_stat_identity(after):
            raise ValueError("EFI loader changed during inspection")
    return {
        "architecture": architecture,
        "machine": machine,
        "subsystem": subsystem,
        "pe_header_checks_passed": True,
        "signature_trust_verified": False,
    }


def verify_installer_readback(
    source: Path,
    destination: Path,
    manifest: dict,
    architecture: str,
    cancelled=lambda: False,
) -> dict:
    """Compare all file bytes, then inspect the selected fallback EFI loader.

    Callers must separately establish native volume/disk identity and layout.
    Neither caller-supplied receipts nor matching file hashes prove a boot.
    """
    if architecture not in EFI_TARGETS:
        raise ValueError("Explicit x64, arm64 or x86 architecture is required")
    for root in (source, destination):
        workspace.preparation.staging._ancestors(root.absolute())
    source, destination = source.resolve(), destination.resolve()
    if (
        source == destination
        or source in destination.parents
        or destination in source.parents
        or os.path.samefile(source, destination)
    ):
        raise ValueError(
            "Source and readback directories must be distinct and nonoverlapping"
        )
    media.verify_media_manifest(source, manifest, cancelled)
    if not media.plan_media(source).get("ready_for_fat32_copy_now"):
        raise ValueError(
            "Source is not structurally prepared for FAT32 installer media"
        )
    actual = media.verify_media_manifest(destination, manifest, cancelled)
    filename = EFI_TARGETS[architecture][0]
    matches = [
        f["path"]
        for f in actual["files"]
        if f["path"].casefold() == "efi/boot/" + filename
    ]
    if len(matches) != 1:
        raise ValueError(
            "Exactly one selected-architecture fallback EFI loader is required"
        )
    if cancelled():
        raise ValueError("Cancelled before EFI inspection")
    loader = inspect_efi_application(destination / matches[0], architecture)
    # Re-read after PE inspection; races or source changes never yield success.
    media.verify_media_manifest(destination, manifest, cancelled)
    media.verify_media_manifest(source, manifest, cancelled)
    if cancelled():
        raise ValueError("Cancelled before readback receipt")
    return {
        "schema": "arcwyre.windows_installer_file_readback.v1",
        "status": "files_and_efi_headers_verified_boot_unproven",
        "manifest_sha256": actual["manifest_sha256"],
        "verified_files": len(actual["files"]),
        "verified_bytes": actual["total_bytes"],
        "efi_loader": {"path": matches[0], **loader},
        "partition_layout_verified": False,
        "disk_identity_verified": False,
        "bcd_verified": False,
        "secure_boot_trust_verified": False,
        "boot_proven": False,
        "write_authorized": False,
        "system_mutations_performed": False,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--readback-root", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--architecture", choices=tuple(EFI_TARGETS), required=True)
    parser.add_argument("--cancel-file", type=Path)
    args = parser.parse_args(argv)
    cancelled = lambda: args.cancel_file is not None and os.path.lexists(
        args.cancel_file
    )
    try:
        with args.manifest.open(encoding="utf-8") as stream:
            manifest = json.load(stream)
        if not isinstance(manifest, dict):
            raise ValueError("Manifest must be a JSON object")
        result = verify_installer_readback(
            args.source_root, args.readback_root, manifest, args.architecture, cancelled
        )
        print(json.dumps(result, sort_keys=True))
        return 0
    except (OSError, ValueError, RuntimeError) as exc:
        print(
            json.dumps(
                {
                    "schema": "arcwyre.windows_installer_file_readback.v1",
                    "status": "cancelled" if cancelled() else "failed",
                    "error": str(exc),
                    "boot_proven": False,
                    "disk_identity_verified": False,
                    "partition_layout_verified": False,
                    "system_mutations_performed": False,
                },
                sort_keys=True,
            )
        )
        return 130 if cancelled() else 2


if __name__ == "__main__":
    raise SystemExit(main())
