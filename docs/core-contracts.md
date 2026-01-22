# Phoenix Core Contracts (v1.0.0)

These contracts define stable interfaces and data formats for host providers,
imaging providers, and workflow definitions.

## Versioning
- `CONTRACTS_VERSION`: 1.0.0 (crate constant)
- `DEVICE_GRAPH_SCHEMA_VERSION`: 1.1.0 (partitions)
- `WORKFLOW_SCHEMA_VERSION`: 1.0.0

## Host Provider (Rust trait)
```rust
pub trait HostProvider {
    fn device_graph(&self) -> CoreResult<DeviceGraph>;
}
```

## Imaging Provider (Rust trait)
```rust
pub trait ImagingProvider {
    type Reader;
    fn open_read_only(&self, disk_id: &str) -> CoreResult<Self::Reader>;
    fn read_exact(
        &self,
        reader: &mut Self::Reader,
        offset: u64,
        length: u64,
    ) -> CoreResult<Vec<u8>>;
}
```

## Workflow Definition (JSON/YAML)
```json
{
  "schema_version": "1.0.0",
  "name": "windows-installer-usb",
  "steps": [
    {
      "id": "select-target",
      "action": "select_disk",
      "params": { "removable_only": true }
    },
    {
      "id": "stage-files",
      "action": "stage_installer",
      "params": { "source_path": "D:/Win11" }
    }
  ]
}
```

## References
- docs/device-graph.md
- docs/no-wrapper-policy.md
