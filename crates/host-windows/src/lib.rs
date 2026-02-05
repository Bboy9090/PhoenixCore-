use anyhow::Result;
use bootforge_core::{DeviceGraph, HostInfo};

pub fn build_device_graph() -> Result<DeviceGraph> {
    // NOTE: This is a stub. Next issues will fill enumeration properly.
    let host = HostInfo {
        os: "windows".to_string(),
        os_version: "unknown".to_string(),
        machine: "unknown".to_string(),
    };
    Ok(DeviceGraph::new(host, vec![]))
}