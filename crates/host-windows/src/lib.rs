use anyhow::Result;
use bootforge_core::{DeviceGraph, HostInfo};
use uuid::Uuid;

pub fn build_device_graph() -> Result<DeviceGraph> {
    // NOTE: This is a stub. Next issues will fill enumeration properly.
    Ok(DeviceGraph {
        graph_id: Uuid::new_v4(),
        host: HostInfo {
            os: "windows".to_string(),
            os_version: "unknown".to_string(),
            machine: "unknown".to_string(),
        },
        disks: vec![],
        generated_at_utc: "now".to_string(),
    })
}