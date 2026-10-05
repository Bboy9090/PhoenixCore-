#!/usr/bin/env python3
"""Plan FAT32/UEFI Windows installation media without modifying the source or a disk."""

from __future__ import annotations

import argparse
import ctypes
import hashlib
import json
import os
import re
import stat
from pathlib import Path
from typing import Any

SCHEMA = "phoenix_key.fat32_windows_media_plan.v1"
FAT32_MAX_FILE_BYTES = (4 * 1024 * 1024 * 1024) - 1
DEFAULT_SPLIT_SIZE_MB = 3800
WIM_HEADER_SIZE = 0xD0
SWM_NAME_RE = re.compile(r"^install(?:(\d+))?\.swm$", re.IGNORECASE)
WINDOWS_RESERVED_NAMES = {"CON", "PRN", "AUX", "NUL", *(f"COM{i}" for i in range(1, 10)), *(f"LPT{i}" for i in range(1, 10))}


class MediaPlanError(RuntimeError):
    """Raised when the source cannot be safely assessed as Windows install media."""


def file_stat_identity(info):
    # On Windows fstat's ctime is change time, while path stat's ctime is
    # creation time. Compare their explicit creation times across acquisition
    # methods and retain descriptor change-time checks separately.
    timestamp = info.st_ctime_ns
    if os.name == "nt":
        timestamp = getattr(info, "st_birthtime_ns", None)
        if timestamp is None:
            raise MediaPlanError("Windows file identity requires explicit creation timestamps (Python 3.12+).")
    return (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, timestamp)


def reject_named_data_streams(path: Path):
    if os.name != "nt":
        return
    class StreamData(ctypes.Structure):
        _fields_ = [("size", ctypes.c_longlong), ("name", ctypes.c_wchar * 296)]
    api = ctypes.WinDLL("kernel32", use_last_error=True)
    first, next_stream, close = api.FindFirstStreamW, api.FindNextStreamW, api.FindClose
    first.argtypes = [ctypes.c_wchar_p, ctypes.c_int, ctypes.POINTER(StreamData), ctypes.c_uint]
    first.restype = ctypes.c_void_p
    next_stream.argtypes = [ctypes.c_void_p, ctypes.POINTER(StreamData)]
    next_stream.restype = ctypes.c_int
    close.argtypes = [ctypes.c_void_p]
    close.restype = ctypes.c_int
    data = StreamData()
    handle = first(str(path), 0, ctypes.byref(data), 0)
    if handle == ctypes.c_void_p(-1).value:
        error = ctypes.get_last_error()
        if error in (38, 87):  # No streams, or filesystem has no stream support.
            return
        raise MediaPlanError(f"Cannot inspect source data streams: WinError {error}")
    try:
        while True:
            if data.name != "::$DATA":
                raise MediaPlanError(f"Named data streams are outside the media manifest: {path}")
            if not next_stream(handle, ctypes.byref(data)):
                error = ctypes.get_last_error()
                if error != 38:
                    raise MediaPlanError(f"Incomplete source stream inventory: WinError {error}")
                break
    finally:
        close(handle)


def capture_media_manifest(root: Path, cancelled=lambda: False) -> dict[str, Any]:
    """Bind an extracted source to actual bytes; this does not certify provenance."""
    if cancelled():
        raise MediaPlanError("Cancelled before manifest inspection.")
    root = root.absolute()
    for ancestor in (root, *root.parents):
        _checked_lstat(ancestor)
    if not stat.S_ISDIR(_checked_lstat(root).st_mode):
        raise MediaPlanError("Manifest source must be a directory.")
    entries = []
    seen = set()
    discovered = []
    for item in _walk_regular_files_nofollow(root):
        if cancelled():
            raise MediaPlanError("Cancelled during manifest discovery.")
        discovered.append(item)
    for path, info in sorted(discovered, key=lambda item: str(item[0])):
        if cancelled():
            raise MediaPlanError("Cancelled during manifest inspection.")
        relative = path.relative_to(root).as_posix()
        if relative.casefold() in seen:
            raise MediaPlanError("Case-colliding media paths are not supported.")
        seen.add(relative.casefold())
        if any(
            part.endswith((".", " "))
            or any(char in part for char in '<>:"\\|?*')
            or any(ord(char) < 32 for char in part)
            or part.split(".")[0].upper() in WINDOWS_RESERVED_NAMES
            for part in Path(relative).parts
        ):
            raise MediaPlanError("Source contains a path unsafe for Windows media.")
        digest = hashlib.sha256()
        reject_named_data_streams(path)
        flags = os.O_RDONLY | getattr(os, "O_BINARY", 0) | getattr(os, "O_NOFOLLOW", 0)
        with os.fdopen(os.open(path, flags), "rb") as stream:
            before = os.fstat(stream.fileno())
            if not stat.S_ISREG(before.st_mode) or (before.st_dev, before.st_ino) != (info.st_dev, info.st_ino):
                raise MediaPlanError("Source file identity changed during inspection.")
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                if cancelled():
                    raise MediaPlanError("Cancelled during manifest hashing.")
                digest.update(chunk)
            after = os.fstat(stream.fileno())
        current = _checked_lstat(path)
        reject_named_data_streams(path)
        if (file_stat_identity(before) != file_stat_identity(after)
                or before.st_ctime_ns != after.st_ctime_ns
                or file_stat_identity(after) != file_stat_identity(current)
                or file_stat_identity(info) != file_stat_identity(current)):
            raise MediaPlanError("Source file changed during hashing.")
        entries.append({"path": relative, "size_bytes": after.st_size, "sha256": digest.hexdigest()})
    if not entries:
        raise MediaPlanError("Source is empty.")
    if cancelled():
        raise MediaPlanError("Cancelled before manifest completion.")
    encoded = json.dumps(entries, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return {"schema": "arcwyre.windows_media_manifest.v1", "files": entries,
            "total_bytes": sum(item["size_bytes"] for item in entries),
            "manifest_sha256": hashlib.sha256(encoded).hexdigest(),
            "provenance_verified": False, "target_disk_modified": False}


REPARSE_POINT_ATTRIBUTE = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)


def _is_link_or_reparse(info: os.stat_result) -> bool:
    return stat.S_ISLNK(info.st_mode) or bool(
        getattr(info, "st_file_attributes", 0) & REPARSE_POINT_ATTRIBUTE
    )


def _checked_lstat(path: Path) -> os.stat_result:
    try:
        info = path.lstat()
    except OSError as exc:
        raise MediaPlanError(f"Cannot inspect media path {path}: {exc}") from exc
    if _is_link_or_reparse(info):
        raise MediaPlanError(
            f"Windows installation media must not contain symbolic links, "
            f"junctions, or reparse points: {path}"
        )
    return info


def _is_directory_nofollow(path: Path) -> bool:
    try:
        info = path.lstat()
    except OSError:
        return False
    if _is_link_or_reparse(info):
        raise MediaPlanError(
            f"Windows installation media must not contain symbolic links, "
            f"junctions, or reparse points: {path}"
        )
    return stat.S_ISDIR(info.st_mode)


def _regular_file_info_nofollow(path: Path) -> os.stat_result | None:
    try:
        info = path.lstat()
    except OSError:
        return None
    if _is_link_or_reparse(info):
        raise MediaPlanError(
            f"Windows installation media must not contain symbolic links, "
            f"junctions, or reparse points: {path}"
        )
    if not stat.S_ISREG(info.st_mode):
        return None
    return info


def _walk_regular_files_nofollow(root: Path):
    stack = [root]
    while stack:
        directory = stack.pop()
        reject_named_data_streams(directory)
        try:
            with os.scandir(directory) as entries:
                for entry in entries:
                    path = Path(entry.path)
                    try:
                        info = path.lstat()  # DirEntry.stat has zero dev/inode on Windows.
                    except OSError as exc:
                        raise MediaPlanError(
                            f"Cannot inspect media path {path}: {exc}"
                        ) from exc
                    if _is_link_or_reparse(info):
                        raise MediaPlanError(
                            "Windows installation media must not contain symbolic "
                            f"links, junctions, or reparse points: {path}"
                        )
                    if stat.S_ISDIR(info.st_mode):
                        stack.append(path)
                    elif stat.S_ISREG(info.st_mode):
                        yield path, info
                    else:
                        raise MediaPlanError(
                            "Windows installation media must contain only regular "
                            f"files and directories; unsupported entry: {path}"
                        )
        except MediaPlanError:
            raise
        except OSError as exc:
            raise MediaPlanError(
                f"Cannot enumerate media directory {directory}: {exc}"
            ) from exc


def sources_dir(root: Path) -> Path:
    for name in ("sources", "Sources"):
        candidate = root / name
        if _is_directory_nofollow(candidate):
            return candidate
    raise MediaPlanError("Windows installation media is missing its Sources directory.")


def first_file(root: Path, names: tuple[str, ...]) -> Path | None:
    for name in names:
        candidate = root / name
        if _regular_file_info_nofollow(candidate) is not None:
            return candidate
    return None


def valid_wim_header(path: Path) -> bool:
    info = _regular_file_info_nofollow(path)
    if info is None or info.st_size < WIM_HEADER_SIZE:
        return False
    flags = os.O_RDONLY | getattr(os, "O_BINARY", 0) | getattr(os, "O_NOFOLLOW", 0)
    try:
        fd = os.open(path, flags)
        with os.fdopen(fd, "rb", closefd=True) as stream:
            opened = os.fstat(stream.fileno())
            if not stat.S_ISREG(opened.st_mode):
                return False
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
    return [
        name
        for name in candidates
        if _regular_file_info_nofollow(root / name) is not None
    ]


def split_wim_segments(sources: Path) -> list[Path]:
    segments: list[Path] = []
    try:
        with os.scandir(sources) as entries:
            for entry in entries:
                path = Path(entry.path)
                try:
                    info = path.lstat()
                except OSError as exc:
                    raise MediaPlanError(
                        f"Cannot inspect media path {path}: {exc}"
                    ) from exc
                if _is_link_or_reparse(info):
                    raise MediaPlanError(
                        "Windows installation media must not contain symbolic "
                        f"links, junctions, or reparse points: {path}"
                    )
                if stat.S_ISREG(info.st_mode) and SWM_NAME_RE.fullmatch(path.name):
                    segments.append(path)
    except MediaPlanError:
        raise
    except OSError as exc:
        raise MediaPlanError(
            f"Cannot enumerate Sources directory {sources}: {exc}"
        ) from exc
    return sorted(
        segments,
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
    for path, info in _walk_regular_files_nofollow(root):
        if info.st_size > FAT32_MAX_FILE_BYTES:
            oversized.append(
                {
                    "path": str(path.relative_to(root)),
                    "size_bytes": info.st_size,
                }
            )
    return oversized


def plan_media(
    root: Path, split_size_mb: int = DEFAULT_SPLIT_SIZE_MB
) -> dict[str, Any]:
    root_info = _checked_lstat(root)
    if not stat.S_ISDIR(root_info.st_mode):
        raise MediaPlanError(
            "Source must be an extracted Windows installation-media folder."
        )
    root = root.resolve()
    if not _is_directory_nofollow(root):
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
    # Never silently choose between competing installation images. A preparation
    # executor must bind one unambiguous source before copying or splitting it.
    if sum((install_wim is not None, install_esd is not None, bool(segments))) > 1:
        block_reasons.append("multiple_windows_install_image_families")
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
        if _regular_file_info_nofollow(install_wim).st_size > FAT32_MAX_FILE_BYTES:
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
        if _regular_file_info_nofollow(install_esd).st_size > FAT32_MAX_FILE_BYTES:
            block_reasons.append("oversized_install_esd_requires_supported_conversion")
    elif segments:
        image_mode = "split_wim"
        contiguous = split_sequence_is_contiguous(segments)
        if not contiguous:
            block_reasons.append("split_wim_sequence_incomplete")
        for path in segments:
            segment_info = _regular_file_info_nofollow(path)
            if segment_info is None:
                block_reasons.append("split_wim_segment_not_regular_file")
                continue
            size = segment_info.st_size
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
        (
            str(install_wim.relative_to(root))
            if install_wim is not None and split_required
            else ""
        )
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


def verify_media_manifest(root: Path, expected: dict[str, Any], cancelled=lambda: False) -> dict[str, Any]:
    """Re-read the complete tree; never accept a caller's hash as proof alone."""
    actual = capture_media_manifest(root, cancelled)
    if expected != actual:
        raise MediaPlanError("Source manifest mismatch: recapture and review the source.")
    return actual


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--capture-manifest", action="store_true")
    parser.add_argument("--verify-manifest", type=Path)
    parser.add_argument(
        "--split-size-mb",
        type=int,
        default=DEFAULT_SPLIT_SIZE_MB,
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result = plan_media(args.source_root, args.split_size_mb)
    if args.verify_manifest:
        expected = json.loads(args.verify_manifest.read_text(encoding="utf-8"))
        result["source_manifest"] = verify_media_manifest(args.source_root, expected)
        result["source_bytes_match_manifest"] = True
    elif args.capture_manifest:
        result["source_manifest"] = capture_media_manifest(args.source_root)
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (MediaPlanError, OSError, ValueError) as exc:
        print(f"FAT32_WINDOWS_MEDIA_PLAN_FAILED: {exc}", file=__import__("sys").stderr)
        raise SystemExit(2) from exc
