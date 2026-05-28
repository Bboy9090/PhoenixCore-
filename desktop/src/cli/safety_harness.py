#!/usr/bin/env python3
"""
Phoenix Core — Safety Validator CLI Integration Harness
A safe, 100% read-only diagnostic utility that queries real host block storage devices,
runs them through the safety classifier, and registers forensic audit records.
"""

import os
import sys
import re
import json
import time
import platform
import subprocess
import plistlib
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

# Ensure we can import the core safety validator module
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from src.core.safety_validator import (
    DeviceProbe,
    SafetyVerdict,
    SafetySeverity,
    classify_device
)


def get_audit_log_path() -> Path:
    """Resolve the forensic audit log path using PHOENIX_SAFETY_AUDIT_PATH or fallbacks"""
    env_path = os.environ.get("PHOENIX_SAFETY_AUDIT_PATH")
    if env_path:
        return Path(env_path)

    # Fallbacks in precedence order
    fallbacks = [
        # 1. Dev workspace scratch path
        Path("/Users/bj90-m1/.gemini/antigravity/brain/502c977f-27e0-4033-913a-921365ab4a5c/scratch/safety_audit.json"),
        # 2. Project-local logs path
        Path(__file__).resolve().parents[3] / "logs" / "safety" / "safety_audit.json",
        # 3. User config log path
        Path.home() / ".config" / "phoenix" / "safety_audit.json",
        # 4. System-wide log folder for packaged builds
        Path("/Library/Logs/Phoenix/safety_audit.json") if platform.system() == "Darwin" else Path("/var/log/phoenix/safety_audit.json")
    ]

    for fb in fallbacks:
        try:
            fb.parent.mkdir(parents=True, exist_ok=True)
            # Try to open/touch it to verify write access
            fb.touch(exist_ok=True)
            return fb
        except Exception:
            continue

    # Ultimate fallback in /tmp
    tmp_path = Path("/tmp/phoenix_safety_audit.json")
    try:
        tmp_path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path.touch(exist_ok=True)
    except Exception:
        pass
    return tmp_path


def persist_audit_record(verdict: SafetyVerdict) -> bool:
    """Write the forensic safety audit log to the active JSONL file.
    Returns True if successfully written, otherwise False (audit_write_failure)."""
    log_path = get_audit_log_path()
    audit_dict = verdict.to_audit_dict()

    # Ensure audit_persistence metadata field is tracked
    if hasattr(verdict, "audit_persistence"):
        audit_dict["audit_persistence"] = verdict.audit_persistence
    else:
        audit_dict["audit_persistence"] = "SUCCESS"

    try:
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(audit_dict) + "\n")
        return True
    except Exception as e:
        # Visible console warning
        RED = "\033[1;31m"
        RESET = "\033[0m"
        print(f"\n{RED}⚠️  WARNING: AUDIT PERSISTENCE FAILURE! Failed to write forensic audit record to {log_path}: {e}{RESET}", file=sys.stderr)
        verdict.audit_persistence = "FAILED"
        return False


def print_styled_verdict(verdict: SafetyVerdict):
    """Print standard color-coded, block-structured output to the console"""
    # ANSI color codes
    RED = "\033[1;31m"
    YELLOW = "\033[1;33m"
    GREEN = "\033[1;32m"
    BLUE = "\033[1;34m"
    RESET = "\033[0m"

    is_safe = (verdict.confidence_score >= 90 and 
               verdict.severity not in (SafetySeverity.SAFETY_CRITICAL_BLOCK, SafetySeverity.SAFETY_BLOCK))

    print("=" * 80)
    if is_safe:
        print(f"{GREEN}✅ Phoenix Safety Clearance Granted {RESET}")
    elif verdict.severity == SafetySeverity.SAFETY_CRITICAL_BLOCK:
        print(f"{RED}🛑 Phoenix Safety Lockout Enforced (CRITICAL) {RESET}")
    else:
        print(f"{RED}🛑 Phoenix Safety Lockout Enforced {RESET}")
    print("=" * 80)

    print(f"Target Device:        {BLUE}{verdict.device_path}{RESET}")
    print(f"Severity Class:       {RED if not is_safe else GREEN}{verdict.severity.value}{RESET}")
    print(f"Confidence Score:     {GREEN if is_safe else RED}{verdict.confidence_score}{RESET} / 90 (Pass Threshold: 90)")
    print(f"Timestamp:            {verdict.timestamp}")

    if not is_safe:
        print("\nReason for Lockout:")
        print(f"{RED}{verdict.hardlock_reason or 'Confidence score below threshold'}{RESET}")
        print("\nOperator Guidance:")
        print(f"{YELLOW}{verdict.operator_message}{RESET}")
    else:
        print("\nClassification Outcome:")
        print(f"{GREEN}{verdict.operator_message}{RESET}")

    if verdict.factors:
        print("\nAttributed Confidence Factors:")
        for factor in verdict.factors:
            color = GREEN if factor.score_delta > 0 else RED
            # Fix sign formatting to prevent float/string exceptions
            print(f"  • [{color}{factor.score_delta:+d}{RESET}] {factor.name}: {factor.description}")

    print("\nForensic Registry Audit Trail:")
    audit_persist = getattr(verdict, "audit_persistence", "SUCCESS")
    if audit_persist == "FAILED":
        print(f"  Audit Persistence:  {RED}FAILED (Forensic evidence was NOT successfully persisted!){RESET}")
    else:
        print(f"  Audit Log Location:  {BLUE}{get_audit_log_path()}{RESET}")
    print("=" * 80)


def probe_device_macos(disk_id: str, root_disk_parent: str, apfs_containers: List[str]) -> DeviceProbe:
    """Execute diskutil plist queries and construct a DeviceProbe on macOS.
    Implements fail-closed heuristics for parser/command uncertainty."""
    device_path = f"/dev/{disk_id}"
    try:
        # Query target details via diskutil info -plist
        result = subprocess.run(
            ["diskutil", "info", "-plist", device_path],
            capture_output=True, check=False, timeout=10
        )
        if result.returncode != 0:
            probe = DeviceProbe(device_path=device_path)
            probe.is_probe_failure = True
            probe.probe_failure_reason = f"diskutil info returned non-zero exit code {result.returncode}"
            probe.is_host_root_parent = True
            return probe

        try:
            plist = plistlib.loads(result.stdout)
        except Exception as pe:
            probe = DeviceProbe(device_path=device_path)
            probe.is_probe_failure = True
            probe.probe_failure_reason = f"Malformed plist output from diskutil: {pe}"
            probe.is_host_root_parent = True
            return probe
        
        whole_disk = plist.get("ParentWholeDisk", disk_id)
        
        # 1. Is active host root parent?
        is_host_root_parent = (whole_disk == root_disk_parent)

        # 2. Is internal SATA or PCIe NVMe?
        device_location = plist.get("DeviceLocation", "Internal")
        bus_protocol = plist.get("BusProtocol", "SATA")
        is_internal_sata_nvme = (
            device_location == "Internal" and 
            bus_protocol in ("SATA", "PCI-Express", "PCI")
        )

        # 3. Is APFS system container backing store?
        is_apfs_system_container = (
            whole_disk in apfs_containers or 
            plist.get("Content") == "Apple_APFS" or
            plist.get("APFSContainerBacking", False)
        )

        # 4. Mounted partitions check
        active_mount_points = []
        mount_point = plist.get("MountPoint", "")
        if mount_point:
            active_mount_points.append(mount_point)

        # If it's a whole disk, query partition mount points manually
        if plist.get("WholeDisk", True):
            # Run df or mount check
            mounts_res = subprocess.run(["mount"], capture_output=True, text=True, check=False)
            if mounts_res.returncode == 0:
                for line in mounts_res.stdout.splitlines():
                    if f"/dev/{disk_id}s" in line:
                        # Extract mount point: "/dev/disk2s1 on /Volumes/BOOT (msdos, local...)"
                        parts = line.split(" on ")
                        if len(parts) >= 2:
                            m_point = parts[1].split(" (")[0]
                            active_mount_points.append(m_point)

        is_removable = plist.get("RemovableMedia", False)
        capacity_bytes = plist.get("Size", 0)
        has_serial = bool(plist.get("DeviceGUID") or plist.get("MediaUUID"))
        has_model = bool(plist.get("DeviceName") or plist.get("MediaName"))

        return DeviceProbe(
            device_path=device_path,
            is_host_root_parent=is_host_root_parent,
            is_internal_sata_nvme=is_internal_sata_nvme,
            is_apfs_system_container=is_apfs_system_container,
            active_mount_points=active_mount_points,
            is_loopback_virtual=(bus_protocol == "Virtual"),
            is_live_session_self=False, # Custom boot check if applicable
            is_removable=is_removable,
            bus_type=bus_protocol.lower(),
            capacity_bytes=capacity_bytes,
            has_serial=has_serial,
            has_model=has_model
        )

    except Exception as e:
        probe = DeviceProbe(device_path=device_path)
        probe.is_probe_failure = True
        probe.probe_failure_reason = f"Exception during macOS disk probing: {e}"
        probe.is_host_root_parent = True
        return probe


def enumerate_macos() -> List[DeviceProbe]:
    """Discover all whole disks and synthesize probes on macOS"""
    probes = []
    
    # 1. Resolve host root's whole parent disk
    root_disk_parent = ""
    root_res = subprocess.run(["diskutil", "info", "-plist", "/"], capture_output=True, check=False)
    if root_res.returncode == 0:
        try:
            plist = plistlib.loads(root_res.stdout)
            root_disk_parent = plist.get("ParentWholeDisk", "")
        except Exception:
            pass

    # 2. Resolve APFS container backing disks
    apfs_containers = []
    apfs_res = subprocess.run(["diskutil", "apfs", "list"], capture_output=True, text=True, check=False)
    if apfs_res.returncode == 0:
        # Match lines like "APFS Container Reference: disk1" or backing stores
        for line in apfs_res.stdout.splitlines():
            if "APFS Container Reference:" in line or "APFS Physical Store" in line:
                match = re.search(r'(disk\d+)', line)
                if match:
                    apfs_containers.append(match.group(1))

    # 3. List all disk identifiers
    list_res = subprocess.run(["diskutil", "list"], capture_output=True, text=True, check=False)
    if list_res.returncode != 0:
        # Fails closed on command failure
        probe = DeviceProbe(device_path="/dev/all_disks")
        probe.is_probe_failure = True
        probe.probe_failure_reason = f"diskutil list returned error exit code {list_res.returncode}"
        probe.is_host_root_parent = True
        return [probe]

    # Find all whole disks anchored securely via /dev/ disk prefix
    identifiers = set(re.findall(r'^/dev/(disk\d+)\b', list_res.stdout, re.MULTILINE))
    for disk_id in sorted(identifiers):
        probe = probe_device_macos(disk_id, root_disk_parent, apfs_containers)
        if probe:
            probes.append(probe)

    return probes


def probe_device_linux(dev_name: str, root_disk_parent: str) -> DeviceProbe:
    """Query sysfs / udev and construct a DeviceProbe on Linux.
    Implements fail-closed heuristics for parser/command uncertainty."""
    device_path = f"/dev/{dev_name}"
    try:
        sys_block_path = Path(f"/sys/block/{dev_name}")
        if not sys_block_path.exists():
            probe = DeviceProbe(device_path=device_path)
            probe.is_probe_failure = True
            probe.probe_failure_reason = f"sysfs block path {sys_block_path} does not exist"
            probe.is_host_root_parent = True
            return probe

        # 1. Is active host root parent?
        is_host_root_parent = (dev_name == root_disk_parent)

        # Query udevadm properties for attributes
        udev_res = subprocess.run(
            ["udevadm", "info", "-q", "property", "-n", device_path],
            capture_output=True, text=True, check=False, timeout=5
        )
        if udev_res.returncode != 0:
            probe = DeviceProbe(device_path=device_path)
            probe.is_probe_failure = True
            probe.probe_failure_reason = f"udevadm info returned exit code {udev_res.returncode}"
            probe.is_host_root_parent = True
            return probe

        udev_props = {}
        for line in udev_res.stdout.splitlines():
            if "=" in line:
                k, v = line.split("=", 1)
                udev_props[k.strip()] = v.strip()

        bus_type = udev_props.get("ID_BUS", "")
        
        try:
            removable_raw = sys_block_path.joinpath("removable").read_text().strip()
        except Exception as re_err:
            probe = DeviceProbe(device_path=device_path)
            probe.is_probe_failure = True
            probe.probe_failure_reason = f"Failed to read sysfs removable attribute: {re_err}"
            probe.is_host_root_parent = True
            return probe

        is_internal_sata_nvme = (
            bus_type in ("ata", "scsi", "nvme") and
            removable_raw != "1"
        )

        is_apfs_system_container = False

        # Read active mount points on partitions of this disk
        active_mount_points = []
        try:
            with open("/proc/mounts", "r", encoding="utf-8") as f:
                for line in f:
                    parts = line.split()
                    if len(parts) >= 2:
                        mount_source = parts[0]
                        mount_point = parts[1]
                        if mount_source.startswith(device_path):
                            active_mount_points.append(mount_point)
        except Exception as mount_err:
            probe = DeviceProbe(device_path=device_path)
            probe.is_probe_failure = True
            probe.probe_failure_reason = f"Failed to read active mounts from /proc/mounts: {mount_err}"
            probe.is_host_root_parent = True
            return probe

        is_loopback_virtual = "virtual" in sys_block_path.resolve().as_posix()
        is_removable = (removable_raw == "1")

        try:
            size_sectors = int(sys_block_path.joinpath("size").read_text().strip())
            capacity_bytes = size_sectors * 512
        except Exception as size_err:
            probe = DeviceProbe(device_path=device_path)
            probe.is_probe_failure = True
            probe.probe_failure_reason = f"Failed to read block capacity size: {size_err}"
            probe.is_host_root_parent = True
            return probe

        has_serial = bool(udev_props.get("ID_SERIAL") or udev_props.get("ID_SERIAL_SHORT"))
        has_model = bool(udev_props.get("ID_MODEL") or udev_props.get("ID_VENDOR"))

        return DeviceProbe(
            device_path=device_path,
            is_host_root_parent=is_host_root_parent,
            is_internal_sata_nvme=is_internal_sata_nvme,
            is_apfs_system_container=is_apfs_system_container,
            active_mount_points=active_mount_points,
            is_loopback_virtual=is_loopback_virtual,
            is_live_session_self=False, # Add live session identification
            is_removable=is_removable,
            bus_type=bus_type.lower(),
            capacity_bytes=capacity_bytes,
            has_serial=has_serial,
            has_model=has_model
        )

    except Exception as e:
        probe = DeviceProbe(device_path=device_path)
        probe.is_probe_failure = True
        probe.probe_failure_reason = f"Exception during Linux disk probing: {e}"
        probe.is_host_root_parent = True
        return probe


def enumerate_linux() -> List[DeviceProbe]:
    """Discover all block devices and synthesize probes on Linux"""
    probes = []

    # 1. Resolve host root's parent disk
    root_disk_parent = ""
    findmnt_res = subprocess.run(["findmnt", "-n", "-o", "SOURCE", "/"], capture_output=True, text=True, check=False)
    if findmnt_res.returncode == 0:
        root_partition = findmnt_res.stdout.strip()
        # Derive parent: /dev/sda1 -> sda, /dev/nvme0n1p2 -> nvme0n1
        root_dev_name = os.path.basename(root_partition)
        if root_dev_name.startswith("nvme"):
            root_disk_parent = root_dev_name.split("p")[0]
        else:
            root_disk_parent = "".join([c for c in root_dev_name if not c.isdigit()])

    # 2. Iterate sysfs block structures
    sys_block = Path("/sys/block")
    if not sys_block.exists():
        # Fails closed on missing sysfs
        probe = DeviceProbe(device_path="/dev/all_disks")
        probe.is_probe_failure = True
        probe.probe_failure_reason = "sysfs block directory /sys/block does not exist"
        probe.is_host_root_parent = True
        return [probe]

    for dev_path in sorted(sys_block.iterdir()):
        dev_name = dev_path.name
        if dev_name.startswith(("sd", "nvme", "loop", "mmcblk")):
            probe = probe_device_linux(dev_name, root_disk_parent)
            if probe:
                probes.append(probe)

    return probes


def run_live_enumeration():
    """Discover and classify all storage devices plugged into the host OS"""
    print("================================================================================")
    print("PHOENIX CORE SAFETY VALIDATOR - LIVE STORAGE DISCOVERY HARNESS")
    print("================================================================================")
    print(f"Host OS Architecture: {platform.system()} ({platform.release()})")
    print(f"Forensic Audit Log:  {get_audit_log_path()}\n")

    sys_type = platform.system()
    if sys_type == "Darwin":
        probes = enumerate_macos()
    elif sys_type == "Linux":
        probes = enumerate_linux()
    else:
        print(f"ERROR: Unsupported host platform: {sys_type}", file=sys.stderr)
        sys.exit(1)

    if not probes:
        print("No block storage devices discovered on host storage bus.")
        return

    # Count duplicates to detect duplicate device model ambiguity
    model_counts = {}
    for p in probes:
        # Combine model and capacity to identify identical device profiles
        key = f"{p.bus_type}_{p.capacity_bytes}"
        model_counts[key] = model_counts.get(key, 0) + 1

    for p in probes:
        # Enforce duplicate ambiguity checks
        key = f"{p.bus_type}_{p.capacity_bytes}"
        p.is_ambiguous_duplicate = (model_counts[key] > 1)

        # Run the core validator
        verdict = classify_device(p)
        
        # 1. Override with custom refusal if probe gathering failed (fail-closed rule)
        if getattr(p, "is_probe_failure", False):
            verdict.severity = SafetySeverity.SAFETY_CRITICAL_BLOCK
            verdict.confidence_score = -1000
            verdict.hardlock_reason = f"Intake validation failed: {getattr(p, 'probe_failure_reason', 'Unknown parser error')}"
            verdict.operator_message = "CRITICAL_ERROR: Probe gathering failed. Uncertainty fails closed to prevent data destruction."

        # 2. Hardlock ambiguous duplicate targets lacking serial descriptors
        if p.is_ambiguous_duplicate and not p.has_serial:
            verdict.severity = SafetySeverity.SAFETY_CRITICAL_BLOCK
            verdict.confidence_score = -500
            verdict.hardlock_reason = "Ambiguous duplicate devices detected with missing hardware serial descriptors"
            verdict.operator_message = "CRITICAL_ERROR: Multiple identical devices found on USB bus but they lack distinct serial numbers. Refusing operation to prevent writing to the wrong target."

        # Persist audit record in JSONL file
        persist_audit_record(verdict)

        # Display block output
        print_styled_verdict(verdict)


def validate_single_target(target_path: str):
    """Diagnose and classify a single targeted path on the live system"""
    print(f"Executing read-only target validation on path: {target_path}...")
    
    sys_type = platform.system()
    probes = []
    if sys_type == "Darwin":
        probes = enumerate_macos()
    elif sys_type == "Linux":
        probes = enumerate_linux()
    else:
        print(f"ERROR: Unsupported host platform: {sys_type}", file=sys.stderr)
        sys.exit(1)

    target_probe = None
    for p in probes:
        if p.device_path == target_path or p.device_path.replace("/dev/", "") == target_path:
            target_probe = p
            break

    if not target_probe:
        print(f"ERROR: Target block device not found on host storage bus: {target_path}", file=sys.stderr)
        sys.exit(1)

    # Count duplicates
    model_counts = {}
    for p in probes:
        key = f"{p.bus_type}_{p.capacity_bytes}"
        model_counts[key] = model_counts.get(key, 0) + 1
    
    key = f"{target_probe.bus_type}_{target_probe.capacity_bytes}"
    target_probe.is_ambiguous_duplicate = (model_counts[key] > 1)

    # Classify
    verdict = classify_device(target_probe)

    # Override with custom refusal if probe gathering failed (fail-closed rule)
    if getattr(target_probe, "is_probe_failure", False):
        verdict.severity = SafetySeverity.SAFETY_CRITICAL_BLOCK
        verdict.confidence_score = -1000
        verdict.hardlock_reason = f"Intake validation failed: {getattr(target_probe, 'probe_failure_reason', 'Unknown parser error')}"
        verdict.operator_message = "CRITICAL_ERROR: Probe gathering failed. Uncertainty fails closed to prevent data destruction."

    # Hardlock ambiguous duplicate targets lacking serial descriptors
    if target_probe.is_ambiguous_duplicate and not target_probe.has_serial:
        verdict.severity = SafetySeverity.SAFETY_CRITICAL_BLOCK
        verdict.confidence_score = -500
        verdict.hardlock_reason = "Ambiguous duplicate devices detected with missing hardware serial descriptors"
        verdict.operator_message = "CRITICAL_ERROR: Multiple identical devices found on USB bus but they lack distinct serial numbers. Refusing operation to prevent writing to the wrong target."

    persist_audit_record(verdict)
    print_styled_verdict(verdict)


def main():
    """CLI Entrypoint for the Integration Harness"""
    import argparse
    parser = argparse.ArgumentParser(
        description="Safe, read-only physical storage validation integration harness."
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--enumerate", action="store_true",
        help="Enumerate and validate all connected storage devices."
    )
    group.add_argument(
        "--validate-target", type=str, metavar="BLOCK_PATH",
        help="Validate a specific target device block path (read-only check)."
    )

    args = parser.parse_args()

    if args.enumerate:
        run_live_enumeration()
    elif args.validate_target:
        validate_single_target(args.validate_target)


if __name__ == "__main__":
    main()
