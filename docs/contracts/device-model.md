# Device Model

Phoenix Agent must use explicit device identity for every storage device.

## Device Identity

Each device response must include:

- `device_id` - Agent-stable identifier for the current host scan.
- `display_name` - human-readable device name.
- `stable_path` - OS path when available.
- `physical_path` - bus/controller path when available.
- `serial` - device serial when available.
- `vendor`
- `model`
- `size_bytes`
- `removable`
- `system_disk`
- `read_only`
- `bus`
- `partition_count`
- `identity_fingerprint`
- `risk_level`

## Device Identity Rules

- UI apps must send `device_id` and `identity_fingerprint` for target operations.
- Phoenix Agent must re-resolve the device before preview and before execution.
- Phoenix Agent must reject mismatched fingerprints.
- Phoenix Agent must mark system disks as protected by default.
- Phoenix Agent must treat missing identity fields as higher risk.

## Removable Drive Listing

`GET /devices/removable` returns only devices that are candidate removable media.

It must still include `system_disk` and `risk_level`; removable does not mean safe.

## Future Sources

Device information may come from:

- `backend/core/device_scanner.py`
- `backend/core/hardware_profiler.py`
- `desktop/src/core/disk_manager.py`
- `desktop/src/core/hardware_detector.py`
- host crates under `crates/host-*`

PR6 does not move those implementations.
