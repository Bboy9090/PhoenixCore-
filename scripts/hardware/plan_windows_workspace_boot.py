"""Read-only UEFI provisioning plan; supplied VHD facts never authorize writes."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
from typing import TypedDict

_spec = importlib.util.spec_from_file_location(
    "_workspace_boot_application", Path(__file__).with_name("prepare_windows_workspace.py"))
application = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(application)


class VhdVolumeFacts(TypedDict):
    disk_unique_id: str
    bus_type: str
    is_boot: bool
    is_system: bool
    partition_style: str
    esp_partition_number: int
    windows_partition_number: int
    esp_filesystem: str
    windows_filesystem: str
    image_path: str


def plan_workspace_boot(receipt: dict, vhd_path: Path,
                        volume_facts: VhdVolumeFacts) -> dict:
    """Verify local applied files and describe future native-owned VHD steps.

    No BCDBoot command or caller-selected drive letter is produced. A native
    executor must independently establish both volume leases immediately before
    each action. Physical media and host BCD/NVRAM operations are outside scope.
    """
    error = application.preparation.staging.StagingError
    if not isinstance(receipt, dict) or receipt.get("schema") != "arcwyre.windows_offline_image_application.v1":
        raise error("An offline image application receipt is required")
    if not isinstance(volume_facts, dict) or any(
        "letter" in str(key).lower() for key in volume_facts
    ):
        raise error("Drive letters cannot be supplied to a boot provisioning plan")
    if receipt.get("raw_disk_operations_performed") is not False:
        raise error("Application receipt must be limited to disposable files")
    workspace = Path(receipt["workspace_directory"]).absolute()
    applied = Path(receipt["applied_directory"]).absolute()
    if applied != workspace / "applied-files":
        raise error("Applied tree must be directly inside its workspace")
    manifest = application.preparation.media.verify_media_manifest(
        applied, receipt["applied_manifest"])
    source_sha = application._hash(workspace / "source.wim")
    if source_sha != receipt.get("source_sha256"):
        raise error("Workspace image no longer matches the application source")
    # Verify required boot template from actual applied bytes, not a receipt flag.
    template = applied / "Windows/System32/config/BCD-Template"
    template_sha = application._hash(template)
    vhd_path = vhd_path.absolute()
    if vhd_path.parent != workspace or vhd_path.suffix.lower() != ".vhdx":
        raise error("VHDX must be directly inside the application workspace")
    vhd_sha = application._hash(vhd_path)
    with application._open_regular(vhd_path) as stream:
        if stream.read(8) != b"vhdxfile":
            raise error("VHDX signature is invalid")
    required = {
        "bus_type": "File Backed Virtual", "is_boot": False,
        "is_system": False, "partition_style": "GPT",
        "esp_filesystem": "FAT32", "windows_filesystem": "NTFS",
        "image_path": str(vhd_path),
    }
    for field, expected in required.items():
        if type(volume_facts.get(field)) is not type(expected) or volume_facts.get(field) != expected:
            raise error(f"VHD facts invalid: {field}")
    partitions = [volume_facts.get("esp_partition_number"),
                  volume_facts.get("windows_partition_number")]
    if any(type(number) is not int or number <= 0 for number in partitions) or partitions[0] == partitions[1]:
        raise error("VHD partitions must be distinct positive indexes")
    unique = volume_facts.get("disk_unique_id")
    if not isinstance(unique, str) or not unique.strip():
        raise error("VHD disk identity is missing")
    binding = {
        "source_sha256": source_sha, "applied_manifest_sha256": manifest["manifest_sha256"],
        "bcd_template_sha256": template_sha, "vhdx_sha256": vhd_sha,
        "volume_facts": dict(volume_facts),
    }
    return {
        "schema": "arcwyre.windows_workspace_boot_plan.v1",
        "binding": binding,
        "plan_sha256": hashlib.sha256(json.dumps(binding, sort_keys=True, separators=(",", ":")).encode()).hexdigest(),
        "steps": [
            {"action": "native-rebind-app-owned-vhd-and-partitions"},
            {"action": "apply-verified-image-to-native-leased-windows-volume"},
            {"action": "configure-uefi-boot-files", "explicit_system_partition": True,
             "firmware_type": "UEFI", "host_nvram_updates": False},
            {"action": "review-offline-internal-disk-san-policy", "proposed_policy": 4},
            {"action": "read-back-files-and-offline-bcd"},
            {"action": "detach-vhd-and-test-in-isolated-vm"},
        ],
        "execution_authorized": False, "physical_writes_authorized": False,
        "boot_proven": False, "windows_to_go_ready": False,
        "unresolved_reasons": ["native_volume_binding_not_observed", "licensing_review",
                               "portable_workspace_support_review", "san_policy_not_applied",
                               "boot_executor_not_run", "isolated_vm_boot_not_tested"],
        "support_note": "Microsoft Windows To Go was removed starting with Windows 10 version 2004; image application does not establish portable workspace support.",
    }
