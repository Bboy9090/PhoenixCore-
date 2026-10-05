"""Prepare oversized install.wim using native Windows DISM in disposable staging.

Microsoft documents that split segments may exceed requested FileSize; actual
segment sizes must therefore be checked. /CheckIntegrity is a tool option, not
independent boot proof. No source images or raw disks are modified.
"""
from __future__ import annotations

import ctypes
import argparse
import importlib.util
import json
import os
from pathlib import Path
import subprocess

_spec = importlib.util.spec_from_file_location(
    "_prepare_staging", Path(__file__).with_name("stage_windows_install_media.py"))
staging = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(staging)
media = staging.media


def _system_dism() -> Path:
    if os.name != "nt":
        raise staging.StagingError("Native Windows DISM is required")
    buffer = ctypes.create_unicode_buffer(32768)
    length = ctypes.windll.kernel32.GetWindowsDirectoryW(buffer, len(buffer))
    if not length or length >= len(buffer):
        raise staging.StagingError("Cannot resolve Windows directory")
    tool = Path(buffer.value) / "System32" / "dism.exe"
    staging._ancestors(tool)
    if not tool.is_file():
        raise staging.StagingError("System DISM is missing")
    return tool


def _run_dism(command, transcript, cancelled):
    with transcript.open("xb") as output:
        process = subprocess.Popen(command, stdout=output, stderr=subprocess.STDOUT,
                                   stdin=subprocess.DEVNULL, shell=False)
        try:
            while process.poll() is None:
                if cancelled():
                    process.terminate()
                    try:
                        process.wait(timeout=10)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        process.wait()
                    raise staging.StagingError("Cancelled during DISM split")
                try:
                    process.wait(timeout=0.1)
                except subprocess.TimeoutExpired:
                    pass
            if process.returncode != 0:
                raise staging.StagingError(f"DISM split failed with exit code {process.returncode}")
        finally:
            if process.poll() is None:
                process.kill()
                process.wait()


def prepare_media(source: Path, staging_parent: Path, name: str, expected_manifest,
                  cancelled=lambda: False, progress=lambda done, total: None):
    plan = media.plan_media(source)
    if not plan["split_required"]:
        receipt = staging.stage_media(source, staging_parent, name, expected_manifest, cancelled, progress)
        workspace = Path(receipt["staging_directory"])
        try:
            prepared = media.verify_media_manifest(workspace, expected_manifest, cancelled)
            media.verify_media_manifest(source, expected_manifest, cancelled)
            if cancelled():
                raise staging.StagingError("Cancelled before preparation receipt", workspace)
            return {**receipt, "schema": "arcwyre.windows_install_preparation.v1",
                    "source_manifest_sha256": expected_manifest["manifest_sha256"],
                    "manifest_sha256": prepared["manifest_sha256"],
                    "verified_bytes": prepared["total_bytes"], "prepared_manifest": prepared,
                    "dism_exit_code": None, "dism_check_integrity_requested": False,
                    "split_structural_checks_passed": False, "split_performed": False,
                    "independent_image_integrity_verified": False, "original_source_modified": False}
        except Exception as exc:
            raise staging.StagingError(str(exc), workspace) from exc
    tool = _system_dism()
    receipt = staging.stage_media(source, staging_parent, name, expected_manifest, cancelled, progress,
                                 _allow_split_required_wim_staging=True)
    workspace = Path(receipt["staging_directory"])
    try:
        # Logs/scratch must remain separate from the prepared media manifest.
        sources = Path(media.plan_media(workspace)["sources_directory"])
        wim = next(workspace / f["path"] for f in expected_manifest["files"]
                   if f["path"].casefold() == "sources/install.wim")
        evidence = workspace.parent / (workspace.name + ".preparation-evidence")
        evidence.mkdir()
        split = evidence / "split"
        split.mkdir()
        command = [str(tool), "/Split-Image", f"/ImageFile:{wim}",
                   f"/SWMFile:{split / 'install.swm'}", "/FileSize:3800", "/CheckIntegrity",
                   f"/LogPath:{split / 'dism.log'}"]
        _run_dism(command, split / "transcript.log", cancelled)
        if cancelled():
            raise staging.StagingError("Cancelled after DISM split")
        segments = list(split.glob("install*.swm"))
        if any(media.SWM_NAME_RE.fullmatch(p.name) is None for p in segments):
            raise staging.StagingError("Unexpected split segment name")
        segments.sort(key=lambda p: int(media.SWM_NAME_RE.fullmatch(p.name).group(1) or 1))
        if not segments or not media.split_sequence_is_contiguous(segments):
            raise staging.StagingError("DISM output sequence is incomplete")
        for segment in segments:
            staging._ancestors(segment)
            if (not media.valid_wim_header(segment)
                    or media._regular_file_info_nofollow(segment).st_size > media.FAT32_MAX_FILE_BYTES):
                raise staging.StagingError("DISM segment structure or FAT32 size is invalid")
        # Verify original copied files before the one intended replacement.
        captured = media.capture_media_manifest(workspace, cancelled)
        if captured != expected_manifest:
            raise staging.StagingError("Staged original files changed during split")
        split_manifest = media.capture_media_manifest(split, cancelled)
        split_hashes = {f["path"]: f for f in split_manifest["files"] if f["path"].endswith(".swm")}
        media.verify_media_manifest(source, expected_manifest, cancelled)
        for segment in segments:
            segment.rename(sources / segment.name)
        wim.unlink()  # Only the disposable verified copy, after valid split output.
        prepared_plan = media.plan_media(workspace)
        if not prepared_plan["ready_for_fat32_copy_now"]:
            raise staging.StagingError("Prepared media remains blocked")
        prepared = media.capture_media_manifest(workspace, cancelled)
        prepared_files = {f["path"]: f for f in prepared["files"]}
        for segment in segments:
            relative = (sources / segment.name).relative_to(workspace).as_posix()
            if prepared_files.get(relative) != {**split_hashes[segment.name], "path": relative}:
                raise staging.StagingError("Split output changed during final preparation")
        originals = {f["path"]: f for f in expected_manifest["files"] if f["path"] != wim.relative_to(workspace).as_posix()}
        if any(prepared_files.get(path) != record for path, record in originals.items()):
            raise staging.StagingError("Unchanged media files changed during preparation")
        media.verify_media_manifest(source, expected_manifest, cancelled)
        if cancelled():
            raise staging.StagingError("Cancelled before preparation receipt", workspace)
        return {**receipt, "schema": "arcwyre.windows_install_preparation.v1",
                "source_manifest_sha256": expected_manifest["manifest_sha256"],
                "manifest_sha256": prepared["manifest_sha256"],
                "verified_bytes": prepared["total_bytes"],
                "prepared_manifest": prepared, "dism_exit_code": 0,
                "split_performed": True,
                "dism_check_integrity_requested": True, "split_structural_checks_passed": True,
                "independent_image_integrity_verified": False, "boot_verified": False,
                "log_directory": str(split), "original_source_modified": False}
    except Exception as exc:
        raise staging.StagingError(str(exc), workspace) from exc


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--staging-parent", type=Path, required=True)
    parser.add_argument("--name", required=True)
    parser.add_argument("--expected-manifest-json", type=Path, required=True,
                        help="Path to the previously captured source manifest JSON")
    parser.add_argument("--cancel-file", type=Path,
                        help="Native-owned signal file; existence requests cancellation")
    args = parser.parse_args(argv)
    try:
        with args.expected_manifest_json.open("r", encoding="utf-8") as stream:
            manifest = json.load(stream)
        cancel = lambda: args.cancel_file is not None and args.cancel_file.exists()
        result = prepare_media(args.source_root, args.staging_parent, args.name, manifest, cancelled=cancel)
        if cancel():
            partial = result.get("staging_directory")
            raise staging.StagingError("Cancelled before CLI result", Path(partial) if partial else None)
        print(json.dumps({"complete": True, **result}, sort_keys=True))
        return 0
    except Exception as exc:
        partial = getattr(exc, "partial_directory", None)
        print(json.dumps({"schema": "arcwyre.windows_install_preparation_failure.v1",
                          "complete": False, "error": str(exc),
                          "unresolved": partial is not None,
                          "partial_directory": str(partial) if partial else None,
                          "cancellation_requested": args.cancel_file is not None and args.cancel_file.exists(),
                          "cancelled": args.cancel_file is not None and args.cancel_file.exists() and "cancel" in str(exc).lower(),
                          "boot_verified": False, "raw_disk_operations_performed": False}, sort_keys=True))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
