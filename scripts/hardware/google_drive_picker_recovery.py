#!/usr/bin/env python3
"""Google Picker desktop OAuth boundary for read-only recovery acquisition."""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import re
import secrets
import time
import urllib.error
import urllib.parse
import urllib.request
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any, Callable

import acquire_google_drive_recovery as drive

AUTH_ENDPOINT = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_ENDPOINT = "https://oauth2.googleapis.com/token"
CLIENT_ID_ENV = "PHOENIX_KEY_GOOGLE_DRIVE_CLIENT_ID"
DRIVE_FILE_SCOPE = "https://www.googleapis.com/auth/drive.file"
CALLBACK_PATH = "/oauth2callback"
CALLBACK_TIMEOUT_SECONDS = 300
SCHEMA = "phoenix_key.google_drive_picker.v1"

UrlOpen = Callable[..., Any]


class PickerError(RuntimeError):
    """Raised when explicit Google Picker authorization cannot be proven."""


def require_client_id(environment: dict[str, str] | None = None) -> str:
    environment = environment if environment is not None else os.environ
    client_id = environment.get(CLIENT_ID_ENV, "").strip()
    if not client_id or not client_id.endswith(".apps.googleusercontent.com"):
        raise PickerError(
            f"Desktop Google OAuth client ID is required in {CLIENT_ID_ENV}."
        )
    return client_id


def code_challenge(verifier: str) -> str:
    if not 43 <= len(verifier) <= 128:
        raise PickerError("PKCE verifier length is outside the OAuth requirement.")
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    return base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")


def build_picker_url(
    *,
    client_id: str,
    redirect_uri: str,
    state: str,
    challenge: str,
) -> str:
    if not redirect_uri.startswith("http://127.0.0.1:"):
        raise PickerError("Desktop Picker redirect must use IPv4 loopback.")
    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": DRIVE_FILE_SCOPE,
        "code_challenge": challenge,
        "code_challenge_method": "S256",
        "state": state,
        "prompt": "consent",
        "trigger_onepick": "true",
        "allow_multiple": "false",
    }
    return f"{AUTH_ENDPOINT}?{urllib.parse.urlencode(params)}"


def parse_picker_callback(query: str, expected_state: str) -> dict[str, str]:
    values = urllib.parse.parse_qs(query, keep_blank_values=True)
    error = values.get("error", [""])[0]
    if error:
        raise PickerError(f"Google Picker authorization failed: {error}")
    if values.get("state", [""])[0] != expected_state:
        raise PickerError("Google Picker callback state did not match the request.")
    code = values.get("code", [""])[0].strip()
    if not code:
        raise PickerError(
            "Google Picker callback did not contain an authorization code."
        )
    picked = values.get("picked_file_ids", [""])[0]
    file_ids = [value.strip() for value in picked.split(",") if value.strip()]
    if len(file_ids) != 1:
        raise PickerError(
            "Google Picker must return exactly one selected recovery file."
        )
    file_id = drive.require_file_id(file_ids[0])
    scopes = set(values.get("scope", [""])[0].split())
    if scopes and scopes != {DRIVE_FILE_SCOPE}:
        raise PickerError("Google Picker returned a scope other than drive.file.")
    return {"code": code, "file_id": file_id, "scope": DRIVE_FILE_SCOPE}


def exchange_code(
    *,
    client_id: str,
    code: str,
    verifier: str,
    redirect_uri: str,
    opener: UrlOpen = urllib.request.urlopen,
) -> str:
    body = urllib.parse.urlencode(
        {
            "client_id": client_id,
            "code": code,
            "code_verifier": verifier,
            "grant_type": "authorization_code",
            "redirect_uri": redirect_uri,
        }
    ).encode("ascii")
    request = urllib.request.Request(
        TOKEN_ENDPOINT,
        data=body,
        headers={
            "Accept": "application/json",
            "Content-Type": "application/x-www-form-urlencoded",
        },
        method="POST",
    )
    try:
        with opener(request) as response:
            payload = drive.read_json_response(response)
    except urllib.error.HTTPError as exc:
        raise PickerError(
            f"Google OAuth token exchange failed with HTTP {exc.code}."
        ) from exc
    except urllib.error.URLError as exc:
        raise PickerError("Google OAuth token exchange was unreachable.") from exc
    token = str(payload.get("access_token") or "").strip()
    if not token:
        raise PickerError("Google OAuth token exchange returned no access token.")
    token_type = str(payload.get("token_type") or "").strip().casefold()
    if token_type != "bearer":
        raise PickerError(
            "Google OAuth token exchange returned an unexpected token type."
        )
    scopes = set(str(payload.get("scope") or DRIVE_FILE_SCOPE).split())
    if scopes != {DRIVE_FILE_SCOPE}:
        raise PickerError("Google OAuth token has a scope other than drive.file.")
    return token


def safe_local_name(provider_name: str, file_id: str) -> str:
    cleaned = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", provider_name).strip(" .")
    if not cleaned:
        cleaned = "google-drive-recovery.bin"
    cleaned = cleaned[:180].rstrip(" .")
    return f"{file_id[:12]}-{cleaned}"


def cancelled_picker_receipt() -> dict[str, Any]:
    return {
        "picker_schema": SCHEMA,
        "operation": "picker",
        "complete": False,
        "cancelled": True,
        "staged_path": None,
        "partial_path": None,
        "read_only": True,
        "cloud_original_modified": False,
        "identity_lock_ready": False,
        "recovery_eligible": False,
        "authorization_scope": DRIVE_FILE_SCOPE,
        "selection_mode": "explicit_google_picker_single_file",
        "oauth_token_persisted": False,
        "oauth_token_exposed_to_ui": False,
        "block_reasons": ["picker_cancelled"],
    }


class PickerCallbackHandler(BaseHTTPRequestHandler):
    callback_query: str | None = None

    def do_GET(self) -> None:
        parsed = urllib.parse.urlsplit(self.path)
        if parsed.path != CALLBACK_PATH:
            self.send_response(404)
            self.end_headers()
            return
        type(self).callback_query = parsed.query
        body = (
            b"Phoenix Key received the Google Drive selection. "
            b"You can close this browser tab and return to Phoenix Key."
        )
        self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: object) -> None:
        return


def picker_download(
    destination_dir: Path,
    *,
    client_id: str,
    browser_open: Callable[..., bool] = webbrowser.open,
    opener: UrlOpen = urllib.request.urlopen,
    progress_file: Path | None = None,
    cancel_file: Path | None = None,
) -> dict[str, Any]:
    destination_dir = destination_dir.resolve()
    destination_dir.mkdir(parents=True, exist_ok=True)
    verifier = secrets.token_urlsafe(64)
    state = secrets.token_urlsafe(32)
    challenge = code_challenge(verifier)
    PickerCallbackHandler.callback_query = None

    with HTTPServer(("127.0.0.1", 0), PickerCallbackHandler) as server:
        server.timeout = 0.5
        port = int(server.server_address[1])
        redirect_uri = f"http://127.0.0.1:{port}{CALLBACK_PATH}"
        authorization_url = build_picker_url(
            client_id=client_id,
            redirect_uri=redirect_uri,
            state=state,
            challenge=challenge,
        )
        if not browser_open(authorization_url, new=2):
            raise PickerError("Phoenix Key could not open the system browser.")
        deadline = time.monotonic() + CALLBACK_TIMEOUT_SECONDS
        while (
            PickerCallbackHandler.callback_query is None and time.monotonic() < deadline
        ):
            if drive.cancel_requested(cancel_file):
                return cancelled_picker_receipt()
            server.handle_request()

    query = PickerCallbackHandler.callback_query
    if not query:
        raise PickerError("Google Picker timed out before a selection was returned.")
    callback = parse_picker_callback(query, state)
    token = exchange_code(
        client_id=client_id,
        code=callback["code"],
        verifier=verifier,
        redirect_uri=redirect_uri,
        opener=opener,
    )
    metadata = drive.get_file_metadata(callback["file_id"], token=token, opener=opener)
    provider_name, _, _ = drive.validate_download_metadata(metadata)
    destination = destination_dir / safe_local_name(provider_name, callback["file_id"])
    if destination.exists():
        raise PickerError("Selected Drive payload already exists at the destination.")
    receipt = drive.download_file(
        callback["file_id"],
        destination,
        token=token,
        opener=opener,
        progress_file=progress_file,
        cancel_file=cancel_file,
    )
    receipt.update(
        {
            "picker_schema": SCHEMA,
            "authorization_scope": DRIVE_FILE_SCOPE,
            "selection_mode": "explicit_google_picker_single_file",
            "oauth_token_persisted": False,
            "oauth_token_exposed_to_ui": False,
        }
    )
    return receipt


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--destination-dir", type=Path, required=True)
    parser.add_argument("--progress-file", type=Path)
    parser.add_argument("--cancel-file", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result = picker_download(
        args.destination_dir,
        client_id=require_client_id(),
        progress_file=args.progress_file,
        cancel_file=args.cancel_file,
    )
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (PickerError, drive.DriveAcquisitionError, OSError, ValueError) as exc:
        print(f"GOOGLE_DRIVE_PICKER_FAILED: {exc}", file=os.sys.stderr)
        raise SystemExit(2) from exc
