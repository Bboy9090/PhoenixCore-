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
      "action": "windows_installer_usb",
      "params": {
        "target_disk_id": "PhysicalDrive1",
        "source_path": "D:/Win11.iso",
        "repartition": true,
        "filesystem": "fat32",
        "driver_source": "D:/Drivers",
        "driver_target": "sources/$OEM$/$1/Drivers",
        "hash_manifest": true,
        "force": true,
        "confirmation_token": "PHX-..."
      }
    },
    {
      "id": "stage-files",
      "action": "report_verify",
      "params": { "path": "reports/<run_id>" }
    }
  ]
}
```

Supported actions:
- `windows_installer_usb`
- `windows_apply_image`
- `linux_installer_usb`
- `macos_installer_usb`
- `report_verify`
- `disk_hash_report`

Example Linux installer step:
```json
{
  "id": "linux-usb",
  "action": "linux_installer_usb",
  "params": {
    "source_path": "/path/to/linux/files",
    "target_mount": "/media/usb",
    "force": true,
    "confirmation_token": "PHX-...",
    "hash_manifest": true
  }
}
```

Workflow runner:
- `phoenix-cli workflow-run --file workflow.json --report-base .`
- Emits a workflow report bundle with step timings + references.

Validate:
- `phoenix-cli workflow-validate --file workflow.yaml`

## Pack Manifest (JSON)
```json
{
  "schema_version": "1.0.0",
  "name": "win11-usb-pack",
  "version": "0.1.0",
  "description": "Windows installer workflows",
  "workflows": ["workflows/installer.json"],
  "assets": "assets/"
}
```

Validate:
- `phoenix-cli pack-validate --manifest pack.json`

Run:
- `phoenix-cli pack-run --manifest pack.json --report-base .`
  - emits pack_report bundle with workflow report paths

Sign:
- `phoenix-cli pack-sign --manifest pack.json --key <hex>`

Verify:
- `phoenix-cli pack-verify --manifest pack.json --key <hex>`

Workflow files can be JSON or YAML.

## References
- docs/device-graph.md
- docs/no-wrapper-policy.md

## Evidence Report Signing
Reports emit `manifest.json` (SHA-256 for key files). When the environment
variable `PHOENIX_SIGNING_KEY` (hex) is present, a `manifest.sig` HMAC-SHA256
signature is produced.

Manifest schema:
- `schema_version`: "1.0.0"

Verification:
- `phoenix-cli report-verify --path reports/<run_id> --key <hex>`

Export:
- `phoenix-cli report-export --path reports/<run_id> --out report.zip`

Verify all reports:
- `phoenix-cli report-verify-tree --root reports --key <hex>`
