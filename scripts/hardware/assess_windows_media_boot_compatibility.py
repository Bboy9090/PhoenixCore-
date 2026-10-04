#!/usr/bin/env python3
"""Read-only advisory assessment. Supplied facts never constitute boot proof."""

from __future__ import annotations

import argparse
import json
from typing import Any

ARCHITECTURES = {"x64", "x86", "arm64"}
BOOT_FILES = {"x64": "bootx64.efi", "x86": "bootia32.efi", "arm64": "bootaa64.efi"}


def assess_boot_compatibility(source: dict[str, Any], computer: dict[str, Any]) -> dict[str, Any]:
    """Assess reported facts; do not authorize writing or certify their provenance.

    Architecture must describe the selected image and firmware architecture,
    respectively. Secure Boot acceptance is machine-specific (including dbx),
    so the presence of an EFI file or a signature alone is insufficient.
    """
    blocked: list[str] = []
    unknown: list[str] = []
    image_arch = source.get("architecture")
    firmware_arch = computer.get("firmware_architecture")
    if image_arch not in ARCHITECTURES:
        unknown.append("selected_image_architecture_unknown")
    if firmware_arch not in ARCHITECTURES:
        unknown.append("computer_firmware_architecture_unknown")
    if image_arch in ARCHITECTURES and firmware_arch in ARCHITECTURES and image_arch != firmware_arch:
        blocked.append("image_firmware_architecture_mismatch")

    mode = computer.get("firmware_mode")
    if mode not in ("uefi", "bios"):
        unknown.append("computer_firmware_mode_unknown")
    elif mode == "bios":
        # This lane currently assesses UEFI installer layouts only.
        blocked.append("bios_layout_not_supported_by_this_assessor")
    else:
        files = source.get("uefi_boot_files")
        if not isinstance(files, list) or not all(isinstance(item, str) for item in files):
            unknown.append("uefi_boot_file_inventory_unknown")
        elif firmware_arch in ARCHITECTURES:
            expected = "efi/boot/" + BOOT_FILES[firmware_arch]
            if expected not in {item.replace("\\", "/").casefold() for item in files}:
                blocked.append("matching_uefi_fallback_loader_missing")

    secure = computer.get("secure_boot_enabled")
    if type(secure) is not bool:
        unknown.append("secure_boot_state_unknown")
    elif secure:
        unknown.append("secure_boot_acceptance_requires_machine_specific_validation")

    for key, missing, invalid in (
        ("required_bytes", "source_capacity_requirement_unknown", "source_capacity_requirement_invalid"),
    ):
        value = source.get(key)
        if value is None:
            unknown.append(missing)
        elif type(value) is not int or value <= 0:
            blocked.append(invalid)
    capacity = computer.get("media_capacity_bytes")
    if capacity is None:
        unknown.append("media_capacity_unknown")
    elif type(capacity) is not int or capacity <= 0:
        blocked.append("media_capacity_invalid")
    required = source.get("required_bytes")
    if type(required) is int and required > 0 and type(capacity) is int and capacity > 0 and capacity < required:
        blocked.append("media_capacity_insufficient")

    return {
        "schema": "arcwyre.windows_media_boot_compatibility.v1",
        "assessment": "blocked" if blocked else "unresolved" if unknown else "reported_facts_compatible",
        "block_reasons": blocked,
        "unresolved_reasons": unknown,
        "boot_proven": False,
        "write_authorized": False,
        "system_mutations_performed": False,
        "evidence_scope": "supplied_facts_only",
        "limitations": ["storage_driver_compatibility_not_assessed", "windows_hardware_requirements_not_assessed", "physical_boot_test_required"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", help="JSON containing source and computer objects")
    args = parser.parse_args()
    with open(args.input, encoding="utf-8") as stream:
        payload = json.load(stream)
    if not isinstance(payload, dict) or not isinstance(payload.get("source"), dict) or not isinstance(payload.get("computer"), dict):
        parser.error("input must contain source and computer objects")
    result = assess_boot_compatibility(payload["source"], payload["computer"])
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["assessment"] == "reported_facts_compatible" else 2


if __name__ == "__main__":
    raise SystemExit(main())
