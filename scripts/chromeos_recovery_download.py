#!/usr/bin/env python3
"""
Download a Chrome OS recovery image ZIP for a given board (hardware codename).

Uses the chromeos-releases-data index (CC-BY) which lists official Google-hosted URLs.
Does not write to USB; download only. See docs/CHROMEOS_RECOVERY.md.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Optional


def _repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _ensure_paths() -> None:
    repo = _repo_root()
    desktop = repo / "desktop"
    for p in (repo, desktop):
        if str(p) not in sys.path:
            sys.path.insert(0, str(p))


def main() -> int:
    _ensure_paths()

    from src.core.chromeos_recovery import (
        ChromeosRecoveryError,
        DEFAULT_INDEX_URL,
        download_recovery_zip,
        fetch_index,
        list_board_names,
        select_recovery_for_board,
    )

    parser = argparse.ArgumentParser(
        description="Download Chrome OS recovery image (metadata from chromeos-releases-data; files from dl.google.com)"
    )
    parser.add_argument(
        "--board",
        help="Chrome OS board name (e.g. octopus, hatch, brya). Required unless --list-boards.",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        help="Output path for the .zip file (default: ./chromeos_<board>_recovery_<platform>.zip)",
    )
    parser.add_argument(
        "--index-url",
        default=DEFAULT_INDEX_URL,
        help=f"Override recovery index JSON URL (default: {DEFAULT_INDEX_URL})",
    )
    parser.add_argument(
        "--list-boards",
        action="store_true",
        help="Print known board keys and exit",
    )
    parser.add_argument("--json", action="store_true", help="Print machine-readable selection + path")
    args = parser.parse_args()

    try:
        index = fetch_index(args.index_url)
    except ChromeosRecoveryError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2

    if args.list_boards:
        print("\n".join(list_board_names(index)))
        return 0

    if not args.board:
        print("error: --board is required (or use --list-boards)", file=sys.stderr)
        return 2

    try:
        sel = select_recovery_for_board(index, args.board)
    except ChromeosRecoveryError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2

    if args.output:
        out = args.output.expanduser().resolve()
    else:
        safe_pv = sel.platform_version.replace(".", "_")
        out = Path.cwd() / f"chromeos_{sel.board.lower()}_recovery_{safe_pv}.zip"

    def _progress(done: int, total: Optional[int]) -> None:
        if total:
            pct = 100.0 * done / total
            print(f"\r  {done / (1024 * 1024):.1f} / {total / (1024 * 1024):.1f} MiB ({pct:.1f}%)", end="", flush=True)
        else:
            print(f"\r  {done / (1024 * 1024):.1f} MiB", end="", flush=True)

    try:
        print(f"Downloading: {sel.url}")
        path = download_recovery_zip(sel.url, out, progress_callback=_progress)
        print()
    except ChromeosRecoveryError as e:
        print(f"\nerror: {e}", file=sys.stderr)
        return 2

    if args.json:
        payload = sel.to_dict()
        payload["path"] = str(path)
        print(json.dumps(payload, indent=2))
    else:
        print(f"Saved: {path}")
        print(f"Board: {sel.board}  platform={sel.platform_version}  chrome={sel.chrome_version}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
