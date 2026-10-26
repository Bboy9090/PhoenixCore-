#!/usr/bin/env python3
"""Emit one integrity-bound ARCWYRE release-evidence receipt."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.release.evaluate_arcwyre_release_gate import (
    GATES,
    SCHEMA,
    canonical_sha256,
    write_json_atomic,
)


def build_receipt(args: argparse.Namespace) -> dict[str, object]:
    payload: dict[str, object] = {
        "schema": SCHEMA,
        "gate": args.gate,
        "status": args.status,
        "source_commit": args.source_commit,
        "executor": args.executor,
        "observed_at": args.observed_at,
        "evidence_uri": args.evidence_uri,
    }
    payload["receipt_sha256"] = canonical_sha256(payload)
    return payload


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gate", choices=GATES, required=True)
    parser.add_argument("--status", choices=("passed", "blocked", "failed"), required=True)
    parser.add_argument("--source-commit", required=True)
    parser.add_argument("--executor", required=True)
    parser.add_argument("--observed-at", required=True)
    parser.add_argument("--evidence-uri", required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    payload = build_receipt(args)
    write_json_atomic(args.output, payload)
    print(json.dumps(payload, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
