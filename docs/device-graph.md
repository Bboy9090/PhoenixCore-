# Device Graph (schema v1.1.0)

Phoenix outputs a stable JSON contract.

Top-level:
- schema_version: "1.0.0"
- graph_id: UUID
- generated_at_utc: RFC3339 string
- host: OS info
- disks: physical disks

Disk:
- id: stable id (Windows: "PhysicalDriveN")
- friendly_name: best-effort
- size_bytes
- removable: best-effort
- is_system_disk: true if contains system volume
- partitions: mapped partitions / mount points

Partition:
- id: stable partition id (Windows: DiskNPartitionM)
- label: filesystem label
- fs: filesystem name
- size_bytes: partition bytes
- mount_points: e.g. ["C:\\", "E:\\"]
# Device Graph Schema

**Version:** 1.0.0

The Device Graph is the foundational data structure that represents the complete state of storage devices on a host system.

## Schema

```json
{
  "graph_id": "uuid-v4",
  "host": {
    "os": "windows|linux|macos",
    "os_version": "string",
    "machine": "string"
  },
  "disks": [
    {
      "id": "string (provider-stable)",
      "friendly_name": "string",
      "size_bytes": 0,
      "is_system_disk": false,
      "removable": false,
      "partitions": [
        {
          "id": "string",
          "label": "string|null",
          "fs": "string|null",
          "size_bytes": 0,
          "mount_points": []
        }
      ]
    }
  ],
  "generated_at_utc": "ISO8601 timestamp"
}
```

## Field Definitions

| Field | Type | Description |
|-------|------|-------------|
| `graph_id` | UUID | Unique identifier for this graph instance |
| `host.os` | string | Operating system: `windows`, `linux`, or `macos` |
| `host.os_version` | string | OS version string |
| `host.machine` | string | Machine identifier |
| `disks[].id` | string | Stable disk identifier (best-effort across runs) |
| `disks[].friendly_name` | string | Human-readable disk name |
| `disks[].size_bytes` | u64 | Total disk size in bytes |
| `disks[].is_system_disk` | bool | Best-effort flag for system/boot disk |
| `disks[].removable` | bool | Whether disk is removable media |
| `partitions[].id` | string | Partition identifier |
| `partitions[].label` | string? | Partition label if available |
| `partitions[].fs` | string? | Filesystem type if detected |
| `partitions[].size_bytes` | u64 | Partition size in bytes |
| `partitions[].mount_points` | array | Active mount points |

## Backward Compatibility

Future versions will add fields without breaking existing consumers. Breaking changes will increment the major version.