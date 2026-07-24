#!/usr/bin/env python3
"""Fail closed when PhoenixCore launch claims cross product boundaries."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

SCHEMA = "bws.phoenixcore-launch-claims/v1"
REQUIRED_PRODUCTS = {"PhoenixCore", "BootForge", "Phoenix Key", "ARCWYRE"}
FORBIDDEN_TRUE_CLAIMS = {
    "production_release",
    "release_candidate",
    "universal_hardware_support",
    "universally_safe_physical_writing",
    "trusted_tool_registry_operational",
    "ownership_or_activation_bypass",
}


class BoundaryError(ValueError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise BoundaryError(message)


def validate_matrix(matrix: dict[str, Any]) -> dict[str, Any]:
    require(matrix.get("schema") == SCHEMA, "schema mismatch")
    require(matrix.get("maturity") == "integrated-prototype", "maturity must remain integrated-prototype")
    products = matrix.get("products")
    require(isinstance(products, dict) and set(products) == REQUIRED_PRODUCTS, "product set mismatch")
    for name, record in products.items():
        require(isinstance(record, dict), f"{name} record must be object")
        require(isinstance(record.get("owns"), list) and record["owns"], f"{name} owns list missing")
        require(isinstance(record.get("does_not_own"), list) and record["does_not_own"], f"{name} does_not_own list missing")
        require(not set(record["owns"]) & set(record["does_not_own"]), f"{name} ownership overlap")

    claims = matrix.get("claims")
    require(isinstance(claims, dict), "claims missing")
    for claim in FORBIDDEN_TRUE_CLAIMS:
        require(claim in claims, f"claim missing: {claim}")
        require(claims[claim] is False, f"unsupported claim enabled: {claim}")

    require(isinstance(matrix.get("supported_foundation"), list) and matrix["supported_foundation"], "supported foundation missing")
    blockers = matrix.get("blockers")
    require(isinstance(blockers, list) and blockers, "launch blockers missing")
    require("issue-135-hardware-validation" in blockers, "hardware blocker missing")
    require("issue-136-tool-registry-trust" in blockers, "tool-registry blocker missing")
    return {"valid": True, "maturity": matrix["maturity"], "launch_eligible": False, "blockers": blockers}


def validate_docs(repo_root: Path) -> None:
    readme = (repo_root / "README.md").read_text(encoding="utf-8")
    boundaries = (repo_root / "docs" / "PRODUCT_BOUNDARIES.md").read_text(encoding="utf-8")
    required_readme = [
        "PhoenixCore does not own the kernel",
        "A successful frontend render is not hardware validation",
        "A commit title such as `v1.0.0-PROD` is not production proof",
    ]
    required_boundaries = [
        "PhoenixCore must not",
        "select a physical target silently",
        "bypass ownership, activation, FRP, MDM, credentials, anti-theft",
        "Each layer preserves upstream identities",
    ]
    for phrase in required_readme:
        require(phrase in readme, f"README boundary phrase missing: {phrase}")
    for phrase in required_boundaries:
        require(phrase in boundaries, f"product-boundary phrase missing: {phrase}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--matrix", type=Path, default=Path("docs/LAUNCH_CLAIMS_MATRIX.json"))
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    root = args.repo_root.resolve()
    matrix = json.loads((root / args.matrix).read_text(encoding="utf-8"))
    report = validate_matrix(matrix)
    validate_docs(root)
    rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
