#!/usr/bin/env python3
"""
BootForge MVP reality check (headless).

This intentionally avoids GUI. It validates:
- phoenix_safety imports
- recipe discovery
- removable-only selection vs. blocking non-removable
- dry-run execution (no destructive writes)
- durable audit record creation (backend/core/audit_store.py)

Use this on a real operator machine to validate the end-to-end product surface.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path


def _repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _ensure_import_paths() -> None:
    repo = _repo_root()
    desktop = repo / "desktop"
    backend = repo / "backend"
    for p in (repo, desktop, backend):
        if str(p) not in sys.path:
            sys.path.insert(0, str(p))


def main() -> int:
    _ensure_import_paths()

    parser = argparse.ArgumentParser(description="BootForge MVP reality check (headless)")
    parser.add_argument("--recipe", default="Custom Payload Deployment", help="Recipe name")
    parser.add_argument("--profile", default="generic_x64", help="Hardware profile id/name")
    parser.add_argument(
        "--device",
        default=None,
        help="Target device path (e.g., /dev/sdb). If omitted, selects first removable device.",
    )
    parser.add_argument(
        "--non-removable-device",
        default="/dev/sda",
        help="A known non-removable candidate to confirm BLOCKED behavior (best-effort).",
    )
    parser.add_argument(
        "--audit-dir",
        default=None,
        help="Override PHOENIX_AUDIT_DIR for this run.",
    )
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON summary")
    args = parser.parse_args()

    if args.audit_dir:
        os.environ["PHOENIX_AUDIT_DIR"] = args.audit_dir

    from src.core.mvp_check import run_mvp_check, MvpCheckConfig

    cfg = MvpCheckConfig(
        recipe_name=args.recipe,
        hardware_profile=args.profile,
        target_device=args.device,
        non_removable_candidate=args.non_removable_device,
        dry_run=True,
    )
    result = run_mvp_check(cfg)

    if args.json:
        print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    else:
        print(result.human_summary())
        if result.errors:
            print("\nErrors:")
            for e in result.errors:
                print(f"- {e}")
        if result.warnings:
            print("\nWarnings:")
            for w in result.warnings:
                print(f"- {w}")

    return 0 if result.ok else 2


if __name__ == "__main__":
    raise SystemExit(main())

