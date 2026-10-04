"""Apply a verified WIM to a newly allocated disposable directory, not a disk.

This is offline file preparation, not Windows To Go provisioning. Boot files,
SAN policy, portability, licensing, and hardware eligibility remain unresolved.
"""
from __future__ import annotations

import hashlib
import argparse
import json
import locale
import importlib.util
import os
from pathlib import Path
import re
import signal
import stat
import tempfile


def _load(name, filename):
    spec = importlib.util.spec_from_file_location(name, Path(__file__).with_name(filename))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


preparation = _load("_workspace_preparation", "prepare_windows_install_media.py")
metadata = _load("_workspace_metadata", "inspect_windows_image_metadata.py")


def _inspect_metadata(tool, args, logs, label, cancelled):
    if cancelled():
        raise preparation.staging.StagingError("Cancelled before image metadata inspection")
    transcript = logs / (label + ".transcript.txt")
    preparation._run_dism(
        [str(tool), "/English", *args, f"/LogPath:{logs / (label + '.log')}"],
        transcript, cancelled,
    )
    return transcript.read_text(encoding=locale.getpreferredencoding(False))


def _open_regular(path):
    preparation.staging._ancestors(path)
    if preparation.media._regular_file_info_nofollow(path) is None:
        raise preparation.staging.StagingError("Source is not a regular file")
    flags = (os.O_RDONLY | getattr(os, "O_BINARY", 0)
             | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0))
    fd = os.open(path, flags)
    if not stat.S_ISREG(os.fstat(fd).st_mode):
        os.close(fd)
        raise preparation.staging.StagingError("Opened source is not a regular file")
    return os.fdopen(fd, "rb")


def _hash(path, cancelled=lambda: False):
    with _open_regular(path) as stream:
        before = os.fstat(stream.fileno())
        digest = hashlib.sha256()
        while chunk := stream.read(1024 * 1024):
            if cancelled():
                raise preparation.staging.StagingError("Cancelled while hashing")
            digest.update(chunk)
        after = os.fstat(stream.fileno())
        def identity(info):
            return (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, info.st_ctime_ns)
        if identity(before) != identity(after) or identity(after) != identity(path.stat()):
            raise preparation.staging.StagingError("File changed while hashing")
        return digest.hexdigest()


def prepare_workspace(source: Path, expected_sha256: str, selected_index: int,
                      cancelled=lambda: False):
    """Allocate output ourselves: callers cannot choose a Windows apply target."""
    error = preparation.staging.StagingError
    if source.suffix.lower() != ".wim":
        raise error("This preparation slice accepts WIM only")
    if type(selected_index) is not int or selected_index < 1:
        raise error("An explicit positive image index is required")
    if not isinstance(expected_sha256, str) or not re.fullmatch(r"[0-9a-fA-F]{64}", expected_sha256):
        raise error("A verified source SHA-256 is required")
    source = source.absolute()
    if _hash(source, cancelled) != expected_sha256.lower():
        raise error("Source image checksum mismatch")
    if not preparation.media.valid_wim_header(source):
        raise error("Source does not have a valid WIM header")
    tool = preparation._system_dism()
    if cancelled():
        raise error("Cancelled before workspace allocation")
    workspace = Path(tempfile.mkdtemp(prefix="arcwyre-offline-image-"))
    try:
        preparation.staging._ancestors(workspace)
        if source == workspace or workspace in source.parents or source in workspace.parents:
            raise error("Source and workspace overlap")
        snapshot = workspace / "source.wim"
        with _open_regular(source) as original, snapshot.open("xb") as copy:
            while chunk := original.read(1024 * 1024):
                if cancelled():
                    raise error("Cancelled while copying image")
                copy.write(chunk)
        if _hash(snapshot, cancelled) != expected_sha256.lower() or _hash(source, cancelled) != expected_sha256.lower():
            raise error("Source changed during snapshot preparation")
        logs = workspace / "logs"
        logs.mkdir()
        def inspect(args, label):
            return _inspect_metadata(tool, args, logs, label, cancelled)
        image_arg = f"/ImageFile:{snapshot}"
        indexes = metadata.parse_index_list(inspect(["/Get-ImageInfo", image_arg], "indexes"))
        if selected_index not in indexes:
            raise error("Selected index is absent from native DISM metadata")
        selected = metadata.parse_detailed_image(inspect(
            ["/Get-ImageInfo", image_arg, f"/Index:{selected_index}"], "selected"), selected_index)
        if not selected["metadata_complete"]:
            raise error("Selected image metadata is incomplete")
        applied = workspace / "applied-files"
        applied.mkdir()
        preparation.staging._ancestors(applied)
        if any(applied.iterdir()) or cancelled():
            raise error("Apply directory is not empty or operation cancelled")
        command = [str(tool), "/English", "/Apply-Image", image_arg,
                   f"/Index:{selected_index}", f"/ApplyDir:{applied}",
                   "/CheckIntegrity", "/Verify", f"/LogPath:{logs / 'apply.log'}"]
        preparation._run_dism(command, logs / "apply.transcript.txt", cancelled)
        if cancelled():
            raise error("Cancelled after image application")
        for relative in ("Windows/System32/ntoskrnl.exe", "Windows/System32/config/SYSTEM",
                         "Windows/System32/config/SOFTWARE"):
            candidate = applied / relative
            preparation.staging._ancestors(candidate)
            if preparation.media._regular_file_info_nofollow(candidate).st_size == 0:
                raise error("Applied Windows tree is incomplete")
        manifest = preparation.media.capture_media_manifest(applied)
        preparation.media.verify_media_manifest(applied, manifest)
        if _hash(snapshot, cancelled) != expected_sha256.lower() or _hash(source, cancelled) != expected_sha256.lower():
            raise error("Source image changed during application")
        return {
            "schema": "arcwyre.windows_offline_image_application.v1",
            "workspace_directory": str(workspace), "applied_directory": str(applied),
            "source_sha256": expected_sha256.lower(), "selected_image": selected,
            "applied_manifest": manifest, "applied_file_readback_bytes": manifest["total_bytes"],
            "dism_exit_code": 0, "check_integrity_requested": True, "verify_requested": True,
            "raw_disk_operations_performed": False, "boot_configuration_performed": False,
            "boot_verified": False, "windows_to_go_ready": False,
            "unresolved_reasons": ["boot_configuration", "san_policy", "portable_workspace_support",
                                   "licensing", "hardware_eligibility", "physical_boot_test"],
            "log_directory": str(logs),
        }
    except Exception as exc:
        raise error(str(exc), workspace) from exc


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("--sha256", required=True)
    parser.add_argument("--index", required=True, type=int)
    args = parser.parse_args(argv)
    cancellation = {"requested": False}
    def request_cancel(signum, frame):
        cancellation["requested"] = True
    previous = {}
    try:
        for signum in (signal.SIGINT, signal.SIGTERM):
            previous[signum] = signal.signal(signum, request_cancel)
        try:
            receipt = prepare_workspace(
                args.source, args.sha256, args.index,
                cancelled=lambda: cancellation["requested"],
            )
            receipt["status"] = "applied_files_verified_boot_unresolved"
            print(json.dumps(receipt, sort_keys=True))
            return 0
        except Exception as exc:
            partial = getattr(exc, "partial_directory", None)
            print(json.dumps({
                "schema": "arcwyre.windows_offline_image_application_failure.v1",
                "status": "cancelled" if cancellation["requested"] else "failed",
                "message": str(exc),
                "partial_directory": str(partial) if partial is not None else None,
                "partial_output_unresolved": partial is not None,
                "raw_disk_operations_performed": False,
                "boot_verified": False,
                "windows_to_go_ready": False,
                "cleanup_performed": False,
            }, sort_keys=True))
            return 130 if cancellation["requested"] else 2
    finally:
        for signum, handler in previous.items():
            signal.signal(signum, handler)


if __name__ == "__main__":
    raise SystemExit(main())
