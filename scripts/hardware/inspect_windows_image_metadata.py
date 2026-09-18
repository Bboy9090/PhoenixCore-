#!/usr/bin/env python3
"""Inspect Windows image metadata with DISM without mounting or modifying images."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Callable

SCHEMA = "phoenix_key.windows_image_metadata.v1"
SUPPORTED_DIRECT_EXTENSIONS = {".wim", ".esd", ".vhd", ".vhdx", ".ffu"}
LOCKED_CONTAINER_EXTENSIONS = {".iso", ".swm"}
INDEX_RE = re.compile(r"(?im)^\s*Index\s*:\s*(\d+)\s*$")
FIELD_RE = re.compile(r"(?im)^\s*([^:\r\n]+?)\s*:\s*(.*?)\s*$")
ARCH_ALIASES = {
    "0": "x86",
    "5": "arm",
    "6": "ia64",
    "9": "x64",
    "12": "arm64",
    "x86": "x86",
    "x64": "x64",
    "amd64": "x64",
    "arm": "arm",
    "arm64": "arm64",
    "aarch64": "arm64",
    "ia64": "ia64",
}


class WindowsImageMetadataError(RuntimeError):
    """Raised when image metadata cannot be inspected safely."""


def normalize_architecture(value: str | None) -> str | None:
    if value is None:
        return None
    key = value.strip().lower()
    return ARCH_ALIASES.get(key, key or None)


def parse_fields(output: str) -> dict[str, str]:
    fields: dict[str, str] = {}
    for match in FIELD_RE.finditer(output):
        key = match.group(1).strip()
        value = match.group(2).strip()
        if key and value:
            fields[key.lower()] = value
    return fields


def parse_index_list(output: str) -> list[int]:
    return sorted({int(value) for value in INDEX_RE.findall(output)})


def parse_detailed_image(output: str, index: int) -> dict[str, Any]:
    fields = parse_fields(output)
    architecture = normalize_architecture(fields.get("architecture"))
    return {
        "index": index,
        "name": fields.get("name"),
        "description": fields.get("description"),
        "architecture": architecture,
        "edition_id": fields.get("edition"),
        "product_name": fields.get("product name"),
        "installation_type": fields.get("installation type"),
        "version": fields.get("version"),
        "service_pack_build": fields.get("servicepack build"),
        "service_pack_level": fields.get("servicepack level"),
        "languages": fields.get("default language"),
        "metadata_complete": bool(
            fields.get("name")
            and architecture
            and fields.get("edition")
        ),
    }


def run_dism(
    args: list[str],
    *,
    runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
) -> str:
    completed = runner(
        ["dism.exe", *args],
        check=False,
        capture_output=True,
        text=True,
        errors="replace",
    )
    if completed.returncode != 0:
        message = (completed.stderr or "").strip() or (completed.stdout or "").strip()
        raise WindowsImageMetadataError(f"DISM metadata inspection failed: {message}")
    return completed.stdout or ""


def inspect_windows_image(
    path: Path,
    *,
    selected_index: int | None = None,
    runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
) -> dict[str, Any]:
    if not path.is_file():
        raise WindowsImageMetadataError(
            "Windows image does not exist or is not a regular file."
        )

    extension = path.suffix.lower()
    if extension in LOCKED_CONTAINER_EXTENSIONS:
        return {
            "schema": SCHEMA,
            "path": str(path.resolve()),
            "extension": extension,
            "metadata_verified": False,
            "selected_index": selected_index,
            "images": [],
            "selection_required": True,
            "restore_eligible": False,
            "block_reasons": [
                (
                    "iso_requires_extracted_install_wim_or_esd"
                    if extension == ".iso"
                    else "split_wim_metadata_requires_complete_set_inspection"
                )
            ],
            "image_modified": False,
        }

    if extension not in SUPPORTED_DIRECT_EXTENSIONS:
        return {
            "schema": SCHEMA,
            "path": str(path.resolve()),
            "extension": extension,
            "metadata_verified": False,
            "selected_index": selected_index,
            "images": [],
            "selection_required": True,
            "restore_eligible": False,
            "block_reasons": ["unsupported_windows_image_metadata_type"],
            "image_modified": False,
        }

    if sys.platform != "win32":
        raise WindowsImageMetadataError(
            "Live Windows image metadata inspection requires Windows DISM."
        )

    image_arg = f"/ImageFile:{path.resolve()}"
    if extension in {".vhd", ".vhdx", ".ffu"}:
        indexes = [1]
    else:
        list_output = run_dism(
            ["/English", "/Get-ImageInfo", image_arg],
            runner=runner,
        )
        indexes = parse_index_list(list_output)

    if not indexes:
        raise WindowsImageMetadataError(
            "DISM did not report any Windows image indexes."
        )

    images: list[dict[str, Any]] = []
    for index in indexes:
        detail_output = run_dism(
            ["/English", "/Get-ImageInfo", image_arg, f"/Index:{index}"],
            runner=runner,
        )
        images.append(parse_detailed_image(detail_output, index))

    index_set = {image["index"] for image in images}
    block_reasons: list[str] = []
    if selected_index is not None and selected_index not in index_set:
        block_reasons.append("selected_index_not_present")

    selection_required = len(images) != 1 and selected_index is None
    if selection_required:
        block_reasons.append("explicit_image_index_selection_required")

    selected = None
    if selected_index is not None:
        selected = next(
            (image for image in images if image["index"] == selected_index),
            None,
        )
    elif len(images) == 1:
        selected = images[0]

    metadata_verified = bool(
        images and all(image["metadata_complete"] for image in images)
    )
    if not metadata_verified:
        block_reasons.append("image_metadata_incomplete")

    if selected is not None and not selected.get("metadata_complete"):
        block_reasons.append("selected_image_metadata_incomplete")

    return {
        "schema": SCHEMA,
        "path": str(path.resolve()),
        "extension": extension,
        "metadata_verified": metadata_verified,
        "selected_index": selected["index"] if selected else selected_index,
        "selected_image": selected,
        "images": images,
        "selection_required": selection_required,
        "restore_eligible": bool(selected and not block_reasons),
        "block_reasons": block_reasons,
        "image_modified": False,
    }


def assess_architecture_compatibility(
    metadata: dict[str, Any],
    target_architecture: str,
) -> dict[str, Any]:
    target = normalize_architecture(target_architecture)
    selected = metadata.get("selected_image")
    source = (
        normalize_architecture(selected.get("architecture"))
        if isinstance(selected, dict)
        else None
    )
    matches = bool(source and target and source == target)
    block_reasons: list[str] = []
    if selected is None:
        block_reasons.append("exact_image_index_not_selected")
    if source is None:
        block_reasons.append("source_architecture_missing")
    if target is None:
        block_reasons.append("target_architecture_missing")
    if source and target and source != target:
        block_reasons.append("source_target_architecture_mismatch")
    return {
        "schema": "phoenix_key.windows_image_architecture_compatibility.v1",
        "source_architecture": source,
        "target_architecture": target,
        "compatible": matches and not block_reasons,
        "block_reasons": block_reasons,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--path", type=Path, required=True)
    parser.add_argument("--index", type=int)
    parser.add_argument("--target-architecture")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    metadata = inspect_windows_image(args.path, selected_index=args.index)
    if args.target_architecture:
        metadata["architecture_compatibility"] = assess_architecture_compatibility(
            metadata,
            args.target_architecture,
        )
        if not metadata["architecture_compatibility"]["compatible"]:
            metadata["restore_eligible"] = False
            metadata["block_reasons"].extend(
                reason
                for reason in metadata["architecture_compatibility"]["block_reasons"]
                if reason not in metadata["block_reasons"]
            )
    print(json.dumps(metadata, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (WindowsImageMetadataError, OSError, ValueError) as exc:
        print(f"WINDOWS_IMAGE_METADATA_FAILED: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc
