# PR41B-B — Safety Validator Integration Harness Specification

This document details the architectural design and validation plan for the **PR41B-B Safety Validator Integration Harness**. The objective of this phase is to construct a safe, read-only wrapper that executes real-world host hardware device enumeration, maps live parameters to the safety classifier data model, prints descriptive validation verdicts, and persists forensic audit trails without allowing any disk writes or destructive operations.

---

## 1. Objectives of the Integration Harness
1. **100% Read-Only Safety**: Ensure that device discovery, classification, and reporting are completely isolated from raw writing, partition table modifications, or sector wiping.
2. **Live Parameter Mapping**: Query real-world host storage buses (using `diskutil`, `lsblk`, `mount`, and `sysfs`) and translate live device characteristics into a `DeviceProbe` structure.
3. **Audit Log Persistence**: Automatically write every real hardware validation run to a persistent local forensic JSON log.
4. **Behavioral Integrity**: Validate correctness against edge cases (APFS synthesized containers, NVMe, mounted partition tables, duplicate hardware vendors) before integrating the validator into active build routines.

---

## 2. Platform-Specific Live Device Mapping
The integration harness defines the exact bridge logic to translate host command outputs into `DeviceProbe` structures:

### macOS Host Mapping (diskutil info Parsing)
The harness executes `diskutil list` to discover disk paths, then queries `diskutil info -plist /dev/[DISK]`:
- **`is_host_root_parent`**: True if target identifier `diskX` is the parent disk of `diskutil info /` (Part of Whole).
- **`is_internal_sata_nvme`**: True if `DeviceLocation == "Internal"` and `BusProtocol` matches `"PCI-Express"` or `"SATA"`.
- **`is_apfs_system_container`**: True if `APFSContainerBacking` tag is true or if `Content` matches `Apple_APFS`.
- **`active_mount_points`**: Appends any mount paths resolved in the plist `MountPoint` or partition mount lists.
- **`is_removable`**: Read directly from `RemovableMedia`.
- **`bus_type`**: Evaluated from `BusProtocol` (normalized to `"usb"`, `"sata"`, `"nvme"`, etc.).
- **`capacity_bytes`**: Parsed from `Size` / `TotalSize`.
- **`has_serial`**: True if `DeviceGUID` or `MediaUUID` is present and valid.
- **`has_model`**: True if `DeviceName` or `MediaName` contains standard strings.

### Linux Host Mapping (sysfs & udevadm Parsing)
The harness parses `/proc/mounts` and queries `udevadm info`:
- **`is_host_root_parent`**: True if target node is the parent of the block path resolved in `findmnt -n -o SOURCE /`.
- **`is_internal_sata_nvme`**: True if `ID_BUS == "ata"` or `ID_BUS == "nvme"` and device is not marked as removable in `/sys/block/[DEV]/removable`.
- **`active_mount_points`**: Extracted by scanning `/proc/mounts` and mapping all mounts belonging to the base disk.
- **`is_loopback_virtual`**: True if `/sys/block/[DEV]/` path resolved links to `/sys/devices/virtual/block/`.
- **`is_removable`**: Parsed directly from `/sys/block/[DEV]/removable` (must equal `1` for removable).
- **`bus_type`**: Normalized from `ID_BUS` or `udevadm` properties.
- **`capacity_bytes`**: Read from `/sys/block/[DEV]/size` (scaled to bytes by multiplying by 512).

---

## 3. CLI Integration Harness Interface
The integration harness will be introduced via a dedicated dry-run utility: `desktop/src/cli/safety_harness.py`.

### Execution Flags
```bash
# Standard Live System Enumeration & Safe dry-run validation
$ python3 desktop/src/cli/safety_harness.py --enumerate

# Validation test of a specific target block path
$ python3 desktop/src/cli/safety_harness.py --validate-target /dev/sdb

# Virtual loopback verification using developer override
$ PHOENIX_SAFETY_DEVELOPER_OVERRIDE=1 python3 desktop/src/cli/safety_harness.py --validate-target /dev/loop0
```

---

## 4. UX Refusal Wording Standards
When a block device fails validation, the harness must render highly descriptive, action-oriented, color-coded refusals:

```
================================================================================
🛑 Phoenix Safety Lockout Enforced 🛑
================================================================================
Target Path:          /dev/sda
Severity Level:       SAFETY_CRITICAL_BLOCK
Confidence Score:     -1000 / 90 (Refusal Threshold: 90)

Reason for Lockout:
Target is the parent disk of the active host OS root mount point.

Operator Guidance:
CRITICAL_ERROR: Device is the active host OS disk and cannot be targeted.
Under no circumstances can raw write operations target internal system disks.
Targeting this drive will brick the developer host machine upon reboot.

Forensic Audit ID:    safety-harness-a9f23d1c
Audit Log Saved:      /Users/bj90-m1/.gemini/antigravity/brain/502c977f-27e0-4033-913a-921365ab4a5c/scratch/safety_audit.json
================================================================================
```

---

## 5. Audit Log Persistence Mechanics
Every dry-run validation execution must write to a structured, newline-delimited JSON audit database file stored under the Scratch artifacts folder:
* **Log Location**: `/Users/bj90-m1/.gemini/antigravity/brain/502c977f-27e0-4033-913a-921365ab4a5c/scratch/safety_audit.json`
* **Log Write Strategy**: Append mode, writing standard forensic validation dictionaries generated via `SafetyVerdict.to_audit_dict()`.

---

## 6. Live Hardware Verification Checklist
The integration harness must be physically run on the local development host to catalog real device configurations and verify safety outputs:

- [ ] **Test APFS Container Isolation**: Execute validation on the host SSD's synthesized slice (`disk1` or similar) to ensure the APFS system container protection triggers `SAFETY_CRITICAL_BLOCK`.
- [ ] **Test Host OS Lockout**: Validate on the primary host parent disk (`disk0` / `/dev/sda`) to ensure the host root protection triggers `SAFETY_CRITICAL_BLOCK`.
- [ ] **Test Active partition mount block**: Plug in the verified USB containing partition mount maps, ensure `active_mount_points` are parsed and trigger `SAFETY_BLOCK`.
- [ ] **Test Ambiguity checks**: Verify duplicate vendor devices trigger `AMBIGUOUS_DUPLICATE` penalty.

---

**Lead Safety Architect**: `Antigravity AI Agent`  
*Current Schema Version:* `1.0.0`
