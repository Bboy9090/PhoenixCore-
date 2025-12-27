use serde::{Deserialize, Serialize};
use uuid::Uuid;

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct DeviceGraph {
    pub graph_id: Uuid,
    pub host: HostInfo,
    pub disks: Vec<Disk>,
    pub generated_at_utc: String,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct HostInfo {
    pub os: String,        // "windows", "linux", "macos"
    pub os_version: String,
    pub machine: String,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct Disk {
    pub id: String,                // stable id per provider
    pub friendly_name: String,
    pub size_bytes: u64,
    pub is_system_disk: bool,      // provider best-effort
    pub removable: bool,
    pub partitions: Vec<Partition>,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct Partition {
    pub id: String,
    pub label: Option<String>,
    pub fs: Option<String>,
    pub size_bytes: u64,
    pub mount_points: Vec<String>,
}
