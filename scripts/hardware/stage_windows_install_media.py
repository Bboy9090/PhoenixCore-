"""Verified installer file staging; never formats or opens a physical drive."""
from __future__ import annotations

import hashlib
import importlib.util
import os
import stat
from pathlib import Path
from typing import Callable, Any

_spec = importlib.util.spec_from_file_location(
    "_staging_media_plan", Path(__file__).with_name("plan_fat32_windows_media.py"))
media = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(media)


class StagingError(RuntimeError):
    def __init__(self, message: str, partial_directory: Path | None = None):
        super().__init__(message)
        self.partial_directory = partial_directory
        self.unresolved = partial_directory is not None


def _ancestors(path: Path) -> None:
    for ancestor in reversed((path, *path.parents)):
        media._checked_lstat(ancestor)


def stage_media(source: Path, staging_parent: Path, name: str,
                expected_manifest: dict[str, Any],
                cancelled: Callable[[], bool] = lambda: False,
                progress: Callable[[int, int], None] = lambda done, total: None,
                *, _allow_split_required_wim_staging: bool = False) -> dict[str, Any]:
    """Create an exclusive directory and copy/read back each file before progress.

    Caller must supply a disposable staging parent, not a device or target volume.
    Interrupted output is retained and must not be treated as bootable media.
    """
    destination = None
    try:
        if ".." in source.parts or ".." in staging_parent.parts:
            raise StagingError("Parent traversal in staging paths is forbidden")
        source, staging_parent = source.absolute(), staging_parent.absolute()
        reserved = {"CON", "PRN", "AUX", "NUL", *(f"COM{i}" for i in range(1, 10)),
                    *(f"LPT{i}" for i in range(1, 10))}
        if (not name or name in (".", "..") or name.endswith((".", " "))
                or name.split(".")[0].upper() in reserved
                or any(c in name for c in '/\\:<>"|?*') or any(ord(c) < 32 for c in name)):
            raise StagingError("Invalid staging directory name")
        _ancestors(source)
        _ancestors(staging_parent)
        if not staging_parent.is_dir():
            raise StagingError("Staging parent must be an existing directory")
        proposed = staging_parent / name
        if proposed == source or proposed in source.parents or source in proposed.parents:
            raise StagingError("Staging destination overlaps source")
        manifest = media.verify_media_manifest(source, expected_manifest)
        plan = media.plan_media(source)
        split_staging = (_allow_split_required_wim_staging
                         and plan["ready_for_fat32_copy_after_split"]
                         and plan["image_mode"] == "install_wim")
        if (not plan["ready_for_fat32_copy_now"] and not split_staging) or plan["block_reasons"]:
            raise StagingError("Source requires preparation or is blocked")
        if cancelled():
            raise StagingError("Cancelled before staging")
        proposed.mkdir()  # Exclusive; existing outputs are never overwritten.
        destination = proposed
        verified = 0
        total = manifest["total_bytes"]
        for record in manifest["files"]:
            if cancelled():
                raise StagingError("Cancelled; staging output is unresolved", destination)
            original = source / record["path"]
            target = destination / record["path"]
            _ancestors(original)
            target.parent.mkdir(parents=True, exist_ok=True)
            _ancestors(target.parent)
            flags = (os.O_RDONLY | getattr(os, "O_BINARY", 0) | getattr(os, "O_NOFOLLOW", 0)
                     | getattr(os, "O_NONBLOCK", 0))
            digest = hashlib.sha256()
            copied = 0
            with os.fdopen(os.open(original, flags), "rb") as input_stream, target.open("xb") as output:
                if not stat.S_ISREG(os.fstat(input_stream.fileno()).st_mode):
                    raise StagingError("Source is no longer a regular file", destination)
                while chunk := input_stream.read(1024 * 1024):
                    if cancelled():
                        raise StagingError("Cancelled; partial file is unverified", destination)
                    output.write(chunk)
                    digest.update(chunk)
                    copied += len(chunk)
                output.flush()
                os.fsync(output.fileno())
            if copied != record["size_bytes"] or digest.hexdigest() != record["sha256"]:
                raise StagingError("Source changed during copy", destination)
            _ancestors(target)
            readback = hashlib.sha256()
            with os.fdopen(os.open(target, flags), "rb") as stream:
                if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
                    raise StagingError("Readback is no longer a regular file", destination)
                for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                    if cancelled():
                        raise StagingError("Cancelled during readback", destination)
                    readback.update(chunk)
            if readback.hexdigest() != record["sha256"]:
                raise StagingError("Readback mismatch", destination)
            verified += copied
            progress(verified, total)
        if cancelled():
            raise StagingError("Cancelled before final verification", destination)
        media.verify_media_manifest(source, manifest)
        media.verify_media_manifest(destination, manifest)
        return {"schema": "arcwyre.windows_install_staging.v1", "staging_directory": str(destination),
                "manifest_sha256": manifest["manifest_sha256"], "verified_bytes": verified,
                "staging_verified": True, "boot_verified": False,
                "raw_disk_operations_performed": False, "staging_files_written": True}
    except StagingError:
        raise
    except Exception as exc:
        raise StagingError(str(exc), destination) from exc
