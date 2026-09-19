#!/usr/bin/env python3
"""Read-only Google Drive recovery acquisition with resumable local download."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Callable

API_BASE = "https://www.googleapis.com/drive/v3"
TOKEN_ENV = "PHOENIX_KEY_GOOGLE_DRIVE_ACCESS_TOKEN"
SCHEMA = "phoenix_key.google_drive_acquisition.v1"
FOLDER_MIME = "application/vnd.google-apps.folder"
GOOGLE_APPS_PREFIX = "application/vnd.google-apps."
FILE_ID_RE = re.compile(r"^[A-Za-z0-9_-]+$")
CHUNK_SIZE = 4 * 1024 * 1024
MAX_LIST_PAGES = 100

UrlOpen = Callable[..., Any]


class DriveAcquisitionError(RuntimeError):
    """Raised when Drive recovery acquisition cannot be proven safe."""


def require_token(environment: dict[str, str] | None = None) -> str:
    environment = environment if environment is not None else os.environ
    token = environment.get(TOKEN_ENV, "").strip()
    if not token:
        raise DriveAcquisitionError(
            f"Google Drive access token is required in {TOKEN_ENV}."
        )
    return token


def require_file_id(value: str, label: str = "file ID") -> str:
    value = value.strip()
    if not FILE_ID_RE.fullmatch(value):
        raise DriveAcquisitionError(f"Google Drive {label} is malformed.")
    return value


def auth_headers(token: str, *, range_start: int | None = None) -> dict[str, str]:
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
    }
    if range_start is not None:
        headers["Range"] = f"bytes={range_start}-"
    return headers


def api_url(path: str, params: dict[str, str] | None = None) -> str:
    query = urllib.parse.urlencode(params or {})
    return f"{API_BASE}/{path}" + (f"?{query}" if query else "")


def read_json_response(response: Any) -> dict[str, Any]:
    try:
        payload = json.loads(response.read().decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise DriveAcquisitionError("Google Drive returned invalid JSON.") from exc
    if not isinstance(payload, dict):
        raise DriveAcquisitionError("Google Drive returned an invalid object.")
    return payload


def get_json(
    path: str,
    *,
    token: str,
    params: dict[str, str] | None = None,
    opener: UrlOpen = urllib.request.urlopen,
) -> dict[str, Any]:
    request = urllib.request.Request(
        api_url(path, params),
        headers=auth_headers(token),
        method="GET",
    )
    try:
        with opener(request) as response:
            return read_json_response(response)
    except urllib.error.HTTPError as exc:
        raise DriveAcquisitionError(
            f"Google Drive read failed with HTTP {exc.code}."
        ) from exc
    except urllib.error.URLError as exc:
        raise DriveAcquisitionError("Google Drive is unreachable.") from exc


def get_file_metadata(
    file_id: str,
    *,
    token: str,
    opener: UrlOpen = urllib.request.urlopen,
    progress_file: Path | None = None,
    cancel_file: Path | None = None,
) -> dict[str, Any]:
    file_id = require_file_id(file_id)
    fields = (
        "id,name,mimeType,size,md5Checksum,modifiedTime,parents,"
        "capabilities(canDownload),resourceKey"
    )
    return get_json(
        f"files/{file_id}",
        token=token,
        params={"fields": fields, "supportsAllDrives": "true"},
        opener=opener,
    )


def escape_drive_query_literal(value: str) -> str:
    return value.replace("\\", "\\\\").replace("'", "\\'")


def list_folder(
    folder_id: str,
    *,
    token: str,
    opener: UrlOpen = urllib.request.urlopen,
) -> dict[str, Any]:
    folder_id = require_file_id(folder_id, "folder ID")
    files: list[dict[str, Any]] = []
    page_token: str | None = None
    for _ in range(MAX_LIST_PAGES):
        params = {
            "q": (
                f"'{escape_drive_query_literal(folder_id)}' in parents and trashed = false"
            ),
            "spaces": "drive",
            "pageSize": "1000",
            "supportsAllDrives": "true",
            "includeItemsFromAllDrives": "true",
            "fields": (
                "nextPageToken,files(id,name,mimeType,size,md5Checksum,"
                "modifiedTime,parents,capabilities(canDownload),resourceKey)"
            ),
        }
        if page_token:
            params["pageToken"] = page_token
        payload = get_json("files", token=token, params=params, opener=opener)
        page_files = payload.get("files", [])
        if not isinstance(page_files, list):
            raise DriveAcquisitionError("Google Drive folder listing is malformed.")
        files.extend(item for item in page_files if isinstance(item, dict))
        next_token = payload.get("nextPageToken")
        if not next_token:
            return {
                "schema": SCHEMA,
                "operation": "list-folder",
                "folder_id": folder_id,
                "files": files,
                "file_count": len(files),
                "read_only": True,
                "cloud_original_modified": False,
            }
        if not isinstance(next_token, str):
            raise DriveAcquisitionError("Google Drive page token is malformed.")
        page_token = next_token
    raise DriveAcquisitionError("Google Drive folder listing exceeded the page limit.")


def file_digest(path: Path, algorithm: str) -> str:
    digest = hashlib.new(algorithm)
    with path.open("rb") as stream:
        while True:
            chunk = stream.read(CHUNK_SIZE)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def validate_download_metadata(metadata: dict[str, Any]) -> tuple[str, int, str | None]:
    mime_type = str(metadata.get("mimeType") or "")
    if mime_type == FOLDER_MIME or mime_type.startswith(GOOGLE_APPS_PREFIX):
        raise DriveAcquisitionError(
            "Recovery acquisition supports stored binary files, not Google Workspace files."
        )
    capabilities = metadata.get("capabilities")
    if (
        not isinstance(capabilities, dict)
        or capabilities.get("canDownload") is not True
    ):
        raise DriveAcquisitionError(
            "Google Drive does not permit downloading this file."
        )
    try:
        size = int(metadata["size"])
    except (KeyError, TypeError, ValueError) as exc:
        raise DriveAcquisitionError("Google Drive file size is unavailable.") from exc
    if size <= 0:
        raise DriveAcquisitionError("Google Drive recovery payload is empty.")
    name = str(metadata.get("name") or "").strip()
    if not name:
        raise DriveAcquisitionError("Google Drive file name is unavailable.")
    md5 = str(metadata.get("md5Checksum") or "").strip().lower() or None
    if md5 is not None and not re.fullmatch(r"[0-9a-f]{32}", md5):
        raise DriveAcquisitionError("Google Drive MD5 metadata is malformed.")
    return name, size, md5


def write_download_progress(
    progress_file: Path | None,
    *,
    phase: str,
    downloaded_size: int,
    provider_size: int,
    resume_offset: int,
) -> None:
    if progress_file is None:
        return
    progress_file.parent.mkdir(parents=True, exist_ok=True)
    percent = min(100.0, (downloaded_size * 100.0) / provider_size)
    payload = {
        "schema": "phoenix_key.google_drive_progress.v1",
        "phase": phase,
        "downloaded_size_bytes": downloaded_size,
        "provider_size_bytes": provider_size,
        "resume_offset_bytes": resume_offset,
        "percent": round(percent, 2),
        "read_only": True,
        "cloud_original_modified": False,
    }
    temporary = progress_file.with_name(progress_file.name + ".tmp")
    temporary.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")
    os.replace(temporary, progress_file)


def cancel_requested(cancel_file: Path | None) -> bool:
    return cancel_file is not None and cancel_file.exists()


def cancelled_download_receipt(
    *,
    file_id: str,
    name: str,
    provider_size: int,
    resume_offset: int,
    partial: Path,
    progress_file: Path | None,
) -> dict[str, Any]:
    observed_size = partial.stat().st_size if partial.exists() else 0
    write_download_progress(
        progress_file,
        phase="cancelled",
        downloaded_size=observed_size,
        provider_size=provider_size,
        resume_offset=resume_offset,
    )
    return {
        "schema": SCHEMA,
        "operation": "download",
        "provider": "google-drive",
        "provider_file_id": file_id,
        "provider_name": name,
        "provider_size_bytes": provider_size,
        "resume_offset_bytes": resume_offset,
        "downloaded_size_bytes": observed_size,
        "complete": False,
        "cancelled": True,
        "staged_path": None,
        "partial_path": str(partial) if partial.exists() else None,
        "read_only": True,
        "cloud_original_modified": False,
        "identity_lock_ready": False,
        "recovery_eligible": False,
        "block_reasons": ["download_cancelled"],
    }


def download_file(
    file_id: str,
    destination: Path,
    *,
    token: str,
    opener: UrlOpen = urllib.request.urlopen,
) -> dict[str, Any]:
    file_id = require_file_id(file_id)
    metadata = get_file_metadata(file_id, token=token, opener=opener)
    name, provider_size, provider_md5 = validate_download_metadata(metadata)

    destination = destination.resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    partial = destination.with_name(destination.name + ".partial")
    if partial.exists() and not partial.is_file():
        raise DriveAcquisitionError(
            "Drive download partial path is not a regular file."
        )
    resume_offset = partial.stat().st_size if partial.exists() else 0
    if resume_offset > provider_size:
        raise DriveAcquisitionError(
            "Drive download partial exceeds provider file size."
        )

    write_download_progress(
        progress_file,
        phase="ready",
        downloaded_size=resume_offset,
        provider_size=provider_size,
        resume_offset=resume_offset,
    )
    if cancel_requested(cancel_file):
        return cancelled_download_receipt(
            file_id=file_id,
            name=name,
            provider_size=provider_size,
            resume_offset=resume_offset,
            partial=partial,
            progress_file=progress_file,
        )

    cancelled = False
    if resume_offset < provider_size:
        params = {"alt": "media", "supportsAllDrives": "true"}
        request = urllib.request.Request(
            api_url(f"files/{file_id}", params),
            headers=auth_headers(
                token, range_start=resume_offset if resume_offset else None
            ),
            method="GET",
        )
        try:
            with opener(request) as response:
                status = int(getattr(response, "status", response.getcode()))
                if resume_offset:
                    content_range = response.headers.get("Content-Range", "")
                    if status != 206 or not content_range.startswith(
                        f"bytes {resume_offset}-"
                    ):
                        raise DriveAcquisitionError(
                            "Google Drive did not honor the resume byte range."
                        )
                    mode = "ab"
                else:
                    if status not in (200, 206):
                        raise DriveAcquisitionError(
                            f"Unexpected Google Drive download status {status}."
                        )
                    mode = "wb"
                with partial.open(mode) as stream:
                    while True:
                        if cancel_requested(cancel_file):
                            cancelled = True
                            break
                        chunk = response.read(CHUNK_SIZE)
                        if not chunk:
                            break
                        stream.write(chunk)
                        write_download_progress(
                            progress_file,
                            phase="downloading",
                            downloaded_size=stream.tell(),
                            provider_size=provider_size,
                            resume_offset=resume_offset,
                        )
                    stream.flush()
                    os.fsync(stream.fileno())
        except urllib.error.HTTPError as exc:
            raise DriveAcquisitionError(
                f"Google Drive download failed with HTTP {exc.code}."
            ) from exc
        except urllib.error.URLError as exc:
            raise DriveAcquisitionError(
                "Google Drive download was interrupted."
            ) from exc

    if cancelled:
        return cancelled_download_receipt(
            file_id=file_id,
            name=name,
            provider_size=provider_size,
            resume_offset=resume_offset,
            partial=partial,
            progress_file=progress_file,
        )

    observed_size = partial.stat().st_size if partial.exists() else 0
    if observed_size != provider_size:
        write_download_progress(
            progress_file,
            phase="incomplete",
            downloaded_size=observed_size,
            provider_size=provider_size,
            resume_offset=resume_offset,
        )
        return {
            "schema": SCHEMA,
            "operation": "download",
            "provider": "google-drive",
            "provider_file_id": file_id,
            "provider_name": name,
            "provider_size_bytes": provider_size,
            "resume_offset_bytes": resume_offset,
            "downloaded_size_bytes": observed_size,
            "complete": False,
            "staged_path": None,
            "partial_path": str(partial),
            "read_only": True,
            "cloud_original_modified": False,
            "block_reasons": ["download_incomplete"],
        }

    observed_md5 = file_digest(partial, "md5")
    observed_sha256 = file_digest(partial, "sha256")
    if provider_md5 and observed_md5 != provider_md5:
        raise DriveAcquisitionError(
            "Downloaded payload does not match Google Drive MD5 metadata."
        )

    os.replace(partial, destination)
    write_download_progress(
        progress_file,
        phase="complete",
        downloaded_size=provider_size,
        provider_size=provider_size,
        resume_offset=resume_offset,
    )
    return {
        "schema": SCHEMA,
        "operation": "download",
        "provider": "google-drive",
        "provider_file_id": file_id,
        "provider_name": name,
        "provider_size_bytes": provider_size,
        "provider_md5": provider_md5,
        "provider_md5_verified": bool(provider_md5),
        "resume_offset_bytes": resume_offset,
        "downloaded_size_bytes": provider_size,
        "observed_md5": observed_md5,
        "observed_sha256": observed_sha256,
        "complete": True,
        "staged_path": str(destination),
        "partial_path": None,
        "read_only": True,
        "cloud_original_modified": False,
        "identity_lock_ready": True,
        "recovery_eligible": False,
        "block_reasons": ["identity_lock_required_before_recovery"],
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="operation", required=True)
    listing = subparsers.add_parser("list-folder")
    listing.add_argument("--folder-id", required=True)
    download = subparsers.add_parser("download")
    download.add_argument("--file-id", required=True)
    download.add_argument("--destination", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    token = require_token()
    if args.operation == "list-folder":
        result = list_folder(args.folder_id, token=token)
    else:
        result = download_file(args.file_id, args.destination, token=token)
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (DriveAcquisitionError, OSError, ValueError) as exc:
        print(f"GOOGLE_DRIVE_ACQUISITION_FAILED: {exc}", file=os.sys.stderr)
        raise SystemExit(2) from exc
