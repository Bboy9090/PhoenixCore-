#!/usr/bin/env python3
"""Fail closed when ARCWYRE Drive is presented as complete without full parity."""

from __future__ import annotations

import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "docs" / "architecture" / "ARCWYRE_DRIVE_CAPABILITY_CONVERGENCE.md"

FORBIDDEN_RELEASE_MARKERS = {
    ROOT
    / "ecosystem"
    / "bootforge_builder.py": ("Successfully simulated hybrid ISO packaging",),
}


def capability_rows(text: str) -> list[tuple[str, str]]:
    rows: list[tuple[str, str]] = []
    for line in text.splitlines():
        if not line.startswith("|") or line.startswith("|---"):
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if len(cells) != 4 or cells[0] == "Capability family":
            continue
        rows.append((cells[0], cells[3]))
    return rows


def main() -> int:
    failures: list[str] = []
    contract_text = CONTRACT.read_text(encoding="utf-8")
    rows = capability_rows(contract_text)

    if not rows:
        failures.append("capability convergence table is missing or unreadable")

    for capability, state in rows:
        if state != "Wired":
            failures.append(f"{capability}: {state}")

    for path, markers in FORBIDDEN_RELEASE_MARKERS.items():
        source = path.read_text(encoding="utf-8")
        for marker in markers:
            if marker in source:
                failures.append(
                    f"release-adjacent source still contains simulated success: "
                    f"{path.relative_to(ROOT)}: {marker}"
                )

    tauri_config = (
        ROOT / "apps" / "phoenix-key" / "src-tauri" / "tauri.conf.json"
    ).read_text(encoding="utf-8")
    if not re.search(r'"productName"\s*:\s*"ARCWYRE Drive"', tauri_config):
        failures.append("desktop package is not branded ARCWYRE Drive")

    if failures:
        print("ARCWYRE_DRIVE_RELEASE_PARITY_BLOCKED")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("ARCWYRE_DRIVE_RELEASE_PARITY_PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
