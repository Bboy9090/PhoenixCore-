# PR41B — Safety Validator Implementation Specification

This document details the technical specification, architectural design, and programmatic blueprints for the **PR41B Safety Validator Engine**. It defines the device classifier pipeline, confidence scoring heuristics, platform-specific command probes, precedence hierarchies, and audit logging structures.

---

## 1. Architectural Overview

The safety validator operates as a stateless policy execution engine written in Python, acting as the single gatekeeper for both CLI and GUI interfaces.

```
       [ Intake Target Block Path ]
                    │
                    ▼
     Stage 1: Platform Probe Gathering ──► (diskutil info / udevadm / mounts)
                    │
                    ▼
     Stage 2: Policy & Assertion Filters ──► (Active Root, Synthetics, Loopback)
                    │
                    ▼
     Stage 3: Confidence Scoring Engine ──► (Calculate points & apply penalties)
                    │
                    ▼
     Stage 4: Enforcement & Hardlock ──► [ PASS (Allow Write) ]
                                      └─► [ BLOCK (Raise SafetyException) ]
```

---

## 2. Confidence Scoring & Decision Matrix

To ensure that the engine refuses to proceed on ambiguous configurations, we define a **Confidence Score (CS)** spanning from `-1000` to `+100`.

* **Absolute Passing Threshold**: **`CS >= 90`**
* **Refusal State**: **`CS < 90`** (Throws immediate `SafetyException` and terminates block write thread).

### Positive Weight Points (Evidence of External USB)
* `+40 points`: Interconnect bus is identified as physical `USB` or `removable SD Card Reader`.
* `+30 points`: Host hardware `removable` media flag is set (`1` / `True`).
* `+20 points`: Physical USB protocol descriptor detected on target bus.
* `+10 points`: Total disk capacity is within the typical flash drive window (`8.0 GB <= capacity <= 256.0 GB`).

### Negative Weight Deductions (Evidence of Internal System Disk)
* `-1000 points`: Device path or any of its sub-partitions matches the active host root mount `/` or `/boot`.
* `-200 points`: Hardware bus interconnect is `PCI-Express` or `NVMe` (internal solid-state storage).
* `-100 points`: APFS Synthesized/APFS Backing Store container mapped to macOS system layout.
* `-100 points`: Device is marked as a fixed internal disk (`removable == False`).
* `-50 points`: Interface type matches `SATA`, `SAS`, or `SCSI` internal controllers.
* `-50 points`: Virtual loopback, RAM-disk, or DM-multipath identifier detected.

---

## 3. Platform-Specific Probes

The engine delegates device attribute gathering to native platform binaries, parsing outputs into a normalized `HostDeviceProfile` object.

### macOS Host Probes
* **Device Characteristics**: parses `diskutil info -plist [DEV]` to read key-value descriptors:
  ```python
  # Target Key-Value Asserts:
  removable = plist['DeviceStorageDescriptor']['RemovableMedia']
  bus_protocol = plist['DeviceStorageDescriptor']['BusProtocol'] # "USB" / "PCI-Express"
  apfs_backing = plist['DeviceStorageDescriptor']['APFSContainerBacking'] # bool
  internal = plist['DeviceLocation'] # "Internal" / "External"
  ```
* **System Containers**: parses `diskutil apfs list` to isolate backing stores for synthesised virtual slices (`disk1`, `disk2`).
* **Active Mounts**: parses `mount` output to check if any active partition slice is registered under `mount -t apfs,hfs`.

### Linux Host Probes
* **Device Characteristics**: parses `/sys/block/[DEV]/` and queries `udevadm`:
  ```bash
  # Query physical udev device properties
  $ udevadm info -q property -n /dev/sdb
  ID_BUS=usb
  ID_USB_DRIVER=usb-storage
  DEVTYPE=disk
  ID_DRIVE_FLASH=1
  ```
* **Removable Flag**: reads `/sys/block/[DEV]/removable` (must return `1` for allowed flash).
* **Active Mounts**: parses `/proc/mounts` and `/proc/self/mountinfo` matching base disk labels to prevent raw overwrite of partitions actively mapped to local directory hierarchies.

---

## 4. Policy Precedence & Pre-flight Flow

Pre-flight safety validation executes the following checks in strict precedence order. If any check fails, the validation routine aborts immediately.

```
       [ Pre-flight Check Initiated ]
                    │
                    ▼
 1. Active Host OS Disk? ──► YES ──► Raise SAFETY_CRITICAL_BLOCK
                    │ NO
                    ▼
 2. Internal SATA/NVMe?  ──► YES ──► Raise SAFETY_CRITICAL_BLOCK
                    │ NO
                    ▼
 3. APFS Synthesized?    ──► YES ──► Raise SAFETY_CRITICAL_BLOCK
                    │ NO
                    ▼
 4. Active Mount Points? ──► YES ──► Raise SAFETY_BLOCK
                    │ NO
                    ▼
 5. Loopback / Virtual?  ──► YES ──► Raise SAFETY_BLOCK
                    │ NO
                    ▼
 6. Confidence Score >= 90? ─► NO ──► Raise SAFETY_BLOCK (Threshold Failure)
                    │ YES
                    ▼
       [ Target Device Validated ]
```

---

## 5. Override & Sandbox Architecture

To enable local developer unit-testing of write paths (e.g., executing test builds targeting virtual loopback nodes) without risking physical host hardware, we define a strict sandboxed override structure.

* **Developer Environment Token**: `PHOENIX_SAFETY_DEVELOPER_OVERRIDE=1`
* **Applicability Bounds**:
  * **Strict Exclusion**: Even if the developer override is active, the engine **MUST NOT** permit writes targeting the active Host OS root disk or internal system PCIe NVMe SSDs.
  * **Allowed Slices**: Overrides are strictly limited to virtual loopback nodes (`/dev/loopX` on Linux) or read-write sparse files. Any attempt to bypass physical SATA or internal PCIe locks using the token triggers a fatal security violation exit.

---

## 6. Logging Semantics & Forensic Audit Trail

To align with our core release blocking principle ("No green check without evidence"), every validation run writes a structured JSON log entry to `/var/log/phoenix-safety.log` or a matching user-space directory.

### Audit Log Schema Example
```json
{
  "timestamp": "2026-05-28T03:45:00Z",
  "engine_version": "1.0.0",
  "target_path": "/dev/sdb",
  "parent_path": "/dev/sdb",
  "execution_context": "pyqt6_desktop_gui",
  "probe_results": {
    "size_bytes": 16000000000,
    "removable": true,
    "bus_protocol": "USB",
    "is_internal": false,
    "active_mounts": ["/media/phoenix/DATA"]
  },
  "confidence_breakdown": {
    "removable_bit": 30,
    "bus_usb": 40,
    "capacity_in_bounds": 10,
    "is_internal_penalty": 0,
    "nvme_penalty": 0,
    "host_root_penalty": 0,
    "apfs_penalty": 0
  },
  "confidence_score": 80,
  "validation_result": "SAFETY_BLOCK",
  "rejection_reason": "Active partition mounts detected on target sdb1: ['/media/phoenix/DATA'].",
  "rejection_severity": "SAFETY_BLOCK"
}
```

---

## 7. GUI & CLI Parity

To prevent safety regressions when transitioning between interfaces, the validation engine is decoupled into a core service layout:

1. **`desktop/src/core/safety_validator.py`**: The single source of truth containing raw platform probes, confidence scoring, and policy filters.
2. **PyQt6 GUI (`desktop/src/gui/`)**: Hooks directly into the `safety_validator.py` device collection routines, mapping `SAFETY_BLOCK` and `SAFETY_CRITICAL_BLOCK` outcomes to disable, color-code, and remove candidates from the GUI combo boxes.
3. **Python CLI (`desktop/src/cli/`)**: Leverages the exact same validator, parsing `SafetyException` states to trigger clean exits with diagnostic JSON dumps for terminal operators.

---

**Lead Safety Engineer**: `Antigravity AI Agent`  
*Current Schema Version:* `1.0.0`
