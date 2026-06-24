# Phase 5B-1: Cross-Platform Device Scanner Consolidation

## Summary

Introduces `device_scanner.py` — a standalone, read-only, cross-platform device detection module that normalizes removable drive information across Windows, macOS, and Linux into a unified schema (`bootforge.device_scan.v2`).

**No physical writing was added. This module only reads device metadata.**

---

## Source Files Reviewed

| File | Source | What Was Extracted |
|------|--------|--------------------|
| `device_scanner.py` (iCloud) | 450 lines, psutil + /sys/block + udevadm | Linux sysfs removable detection, udevadm serial fallback, vendor/model parsing, /proc/mounts system drive check |
| `bootforge.py` (iCloud) | 333 lines, dry-run-only MVP | macOS `diskutil list -plist external physical` pattern, `diskutil info -plist` field mapping, Windows `Get-CimInstance Win32_DiskDrive` via PowerShell |

### What Was Rejected

- `psutil` dependency — removed; PhoenixCore doesn't require it and the sysfs/udevadm approach is more reliable
- `app_utils.py` imports — project-specific utility from ChatGPT project, not applicable
- `_assess_risk()` — replaced with explicit `is_eligible` flag based on safety rules
- `_get_partitions_linux()` — partition enumeration not needed for this phase
- `write_speed_mbps`, `health_status` fields — not reliably detectable, removed
- Logging via `logging.getLogger` — PhoenixCore uses its own `_log()` pattern

---

## Platform Detection Behavior

### Windows (`win32`)
- PowerShell `Get-CimInstance Win32_DiskDrive` with `-NoProfile`
- Fields: DeviceID, Model, SerialNumber, Size, MediaType, InterfaceType
- USB/SD/1394 interface types marked as removable
- Fixed media types marked as fixed/internal

### macOS (`darwin`)
- `diskutil list -plist external physical` (falls back to `diskutil list -plist`)
- `diskutil info -plist <disk_id>` per WholeDisks entry
- Fields: Removable, RemovableMedia, External, Internal, SystemImage, TotalSize, MediaName, VolumeName, FilesystemType, BusProtocol, IORegistryEntryName

### Linux
- Primary: `/sys/block/<device>/removable`, `size`, `device/vendor`, `device/model`, `device/serial`
- Serial fallback: `udevadm info --query=property --name=/dev/<device>` → `ID_SERIAL`
- System drive check: `/proc/mounts` root mount detection
- Fallback: `lsblk -J -o NAME,SIZE,RM,LABEL,FSTYPE,MOUNTPOINT`

---

## Safety Behavior

- All detection is read-only subprocess calls or sysfs reads
- No destructive command call sites exist in the module
- Command failures return safe degraded results with warnings, never crash
- Missing serial/stable ID lowers confidence score
- Fixed/internal/system drives are always marked ineligible with block reasons
- Zero-size drives are blocked
- No auto-selection of targets
- Plain paths not in scan results return None from `get_device_by_path()`

---

## Normalized Output Fields

| Field | Type | Description |
|-------|------|-------------|
| `drive_path` | string | OS device path |
| `display_name` | string | Human-readable name |
| `stable_id` | string/null | Platform-prefixed stable identifier |
| `serial` | string/null | Hardware serial number |
| `size_bytes` | int | Drive capacity |
| `size_gb` | float | Capacity in GB |
| `size_human` | string | Human-readable size |
| `filesystem` | string/null | Detected filesystem |
| `volume_label` | string/null | Volume label |
| `is_removable` | bool | Removable media flag |
| `is_external` | bool | External connection flag |
| `is_fixed` | bool | Fixed/internal flag |
| `is_system` | bool | System/boot drive flag |
| `bus_protocol` | string/null | Connection bus (USB, SCSI, etc.) |
| `platform` | string | Detecting platform |
| `detection_source` | string | Detection method used |
| `confidence` | string | high/medium/low |
| `is_eligible` | bool | Safe for write operations |
| `warnings` | list | Non-blocking warnings |
| `block_reasons` | list | Reasons drive is ineligible |

---

## Test Results

- **37/37 tests pass** in `tests/test_device_scanner.py`
- Tests cover: Windows PS parsing (multi/single/empty), macOS plist parsing (removable/system/invalid), Linux udevadm parsing, device record normalization, confidence levels, eligibility rules, command failure safety, ambiguous target blocking, destructive call site scan, dashboard forbidden label scan

## Dashboard Build

- Passed (no dashboard changes in this phase)

## Danger Scan

- `device_scanner.py`: No hits for destructive commands
- `dashboard/src/App.jsx`: No forbidden UI labels

---

## Explicit Safety Statements

- No physical writing was added in this phase
- No destructive disk operations exist in `device_scanner.py`
- Dashboard was not modified
- Dashboard cannot start physical writes
- Fixed, internal, and system drives are always marked ineligible
