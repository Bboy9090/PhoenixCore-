#!/usr/bin/env python3
"""Plan FAT32/UEFI Windows installation media without modifying the source or a disk."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

SCHEMA = "phoenix_key.fat32_windows_media_plan.v1"
FAT32_MAX_FILE_BYTES = (4 * 1024 * 1024 * 1024) - 1
DEFAULT_SPLIT_SIZE_MB = 3800
WIM_HEADER_SIZE = 0xD0
SWM_NAME_RE = re.compile(r"^install(?:(\d+))?\.swm$", re.IGNORECASE)


class MediaPlanError(RuntimeError):
    """Raised when the source cannot be safely assessed as Windows install media."""


def sources_dir(root: Path) -> Path:
    for name in ("sources", "Sources"):
        candidate = root / name
        if candidate.is_dir():
            return candidate
    raise MediaPlanError("Windows installation media is missing its Sources directory.")


def first_file(root: Path, names: tuple[str, ...]) -> Path | None:
    for name in names:
        candidate = root / name
        if candidate.is_file():
            return candidate
    return None


def valid_wim_header(path: Path) -> bool:
    try:
        if path.stat().st_size < WIM_HEADER_SIZE:
            return False
        with path.open("rb") as stream:
            header = stream.read(WIM_HEADER_SIZE)
    except OSError:
        return False
    if not header.startswith(b"MSWIM\0\0\0"):
        return False
    return int.from_bytes(header[8:12], "little") == WIM_HEADER_SIZE


def uefi_boot_files(root: Path) -> list[str]:
    candidates = (
        "EFI/Boot/bootx64.efi",
        "EFI/Boot/bootaa64.efi",
        "EFI/Boot/bootia32.efi",
        "efi/boot/bootx64.efi",
        "efi/boot/bootaa64.efi",
        "efi/boot/bootia32.efi",
    )
    return [name for name in candidates if (root / name).is_file()]


def split_wim_segments(sources: Path) -> list[Path]:
    return sorted(
        (
            path
            for path in sources.iterdir()
            if path.is_file() and SWM_NAME_RE.fullmatch(path.name)
        ),
        key=lambda path: (
            1
            if SWM_NAME_RE.fullmatch(path.name).group(1) is None
            else int(SWM_NAME_RE.fullmatch(path.name).group(1))
        ),
    )


def split_sequence_is_contiguous(segments: list[Path]) -> bool:
    if len(segments) < 2 or segments[0].name.casefold() != "install.swm":
        return False
    expected = ["install.swm"] + [
        f"install{index}.swm" for index in range(2, len(segments) + 1)
    ]
    return [path.name.casefold() for path in segments] == expected


def oversized_files(root: Path) -> list[dict[str, Any]]:
    oversized: list[dict[str, Any]] = []
    for path in root.rglob("*"):
        if path.is_symlink():
            raise MediaPlanError(
                "Windows installation media must not contain symbolic links."
            )
        if not path.is_file():
            continue
        try:
            size = path.stat().st_size
        except OSError as exc:
            raise MediaPlanError(f"Cannot inspect media file {path}: {exc}") from exc
        if size > FAT32_MAX_FILE_BYTES:
            oversized.append(
                {
                    "path": str(path.relative_to(root)),
                    "size_bytes": size,
                }
            )
    return oversized


def plan_media(
    root: Path, split_size_mb: int = DEFAULT_SPLIT_SIZE_MB
) -> dict[str, Any]:
    if root.is_symlink():
        raise MediaPlanError(
            "Windows installation-media root must not be a symbolic link."
        )
    root = root.resolve()
    if not root.is_dir():
        raise MediaPlanError(
            "Source must be an extracted Windows installation-media folder."
        )
    if not 512 <= split_size_mb <= 4000:
        raise MediaPlanError("Split size must be between 512 MB and 4000 MB.")

    sources = sources_dir(root)
    setup = first_file(root, ("setup.exe", "Setup.exe"))
    boot_wim = first_file(sources, ("boot.wim", "Boot.wim"))
    install_wim = first_file(sources, ("install.wim", "Install.wim"))
    install_esd = first_file(sources, ("install.esd", "Install.esd"))
    segments = split_wim_segments(sources)
    uefi_files = uefi_boot_files(root)
    large_files = oversized_files(root)

    block_reasons: list[str] = []
    if setup is None:
        block_reasons.append("setup_exe_missing")
    if boot_wim is None:
        block_reasons.append("boot_wim_missing")
    elif not valid_wim_header(boot_wim):
        block_reasons.append("boot_wim_structure_invalid")
    if not uefi_files:
        block_reasons.append("uefi_boot_file_missing")

    image_mode = "missing"
    split_required = False
    split_command: list[str] | None = None
    segment_evidence: list[dict[str, Any]] = []

    if install_wim is not None:
        image_mode = "install_wim"
        if not valid_wim_header(install_wim):
            block_reasons.append("install_wim_structure_invalid")
        if install_wim.stat().st_size > FAT32_MAX_FILE_BYTES:
            split_required = True
            split_command = [
                "Dism",
                "/Split-Image",
                f"/ImageFile:{install_wim}",
                f"/SWMFile:{sources / 'install.swm'}",
                f"/FileSize:{split_size_mb}",
                "/CheckIntegrity",
            ]
    elif install_esd is not None:
        image_mode = "install_esd"
        if not valid_wim_header(install_esd):
            block_reasons.append("install_esd_structure_invalid")
        if install_esd.stat().st_size > FAT32_MAX_FILE_BYTES:
            block_reasons.append("oversized_install_esd_requires_supported_conversion")
    elif segments:
        image_mode = "split_wim"
        contiguous = split_sequence_is_contiguous(segments)
        if not contiguous:
            block_reasons.append("split_wim_sequence_incomplete")
        for path in segments:
            size = path.stat().st_size
            valid = valid_wim_header(path)
            segment_evidence.append(
                {
                    "name": path.name,
                    "size_bytes": size,
                    "wim_header_valid": valid,
                    "fat32_size_safe": size <= FAT32_MAX_FILE_BYTES,
                }
            )
            if not valid:
                block_reasons.append("split_wim_structure_invalid")
            if size > FAT32_MAX_FILE_BYTES:
                block_reasons.append("split_wim_segment_exceeds_fat32_limit")
    else:
        block_reasons.append("windows_install_image_missing")

    permitted_oversized = {
        str(install_wim.relative_to(root))
        if install_wim is not None and split_required
        else ""
    }
    unsupported_large = [
        item for item in large_files if item["path"] not in permitted_oversized
    ]
    if unsupported_large:
        block_reasons.append("other_media_file_exceeds_fat32_limit")

    block_reasons = list(dict.fromkeys(block_reasons))
    ready_after_split = (
        split_required
        and not [reason for reason in block_reasons if reason != "fat32_split_required"]
        and not unsupported_large
    )
    ready_now = not block_reasons and not split_required

    return {
        "schema": SCHEMA,
        "source_root": str(root),
        "sources_directory": str(sources),
        "filesystem": "FAT32",
        "uefi_boot_files": uefi_files,
        "uefi_boot_evidence_present": bool(uefi_files),
        "image_mode": image_mode,
        "fat32_max_file_bytes": FAT32_MAX_FILE_BYTES,
        "split_size_mb": split_size_mb,
        "split_required": split_required,
        "split_command_preview": split_command,
        "split_segments": segment_evidence,
        "oversized_files": large_files,
        "unsupported_oversized_files": unsupported_large,
        "ready_for_fat32_copy_now": ready_now,
        "ready_for_fat32_copy_after_split": ready_after_split,
        "block_reasons": block_reasons,
        "source_modified": False,
        "target_disk_modified": False,
        "execution_performed": False,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument(
        "--split-size-mb",
        type=int,
        default=DEFAULT_SPLIT_SIZE_MB,
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    print(json.dumps(plan_media(args.source_root, args.split_size_mb), sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (MediaPlanError, OSError, ValueError) as exc:
        print(f"FAT32_WINDOWS_MEDIA_PLAN_FAILED: {exc}", file=__import__("sys").stderr)
        raise SystemExit(2) from exc
