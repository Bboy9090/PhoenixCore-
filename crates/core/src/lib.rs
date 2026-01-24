use serde::{Deserialize, Serialize};
use time::format_description::well_known::Rfc3339;
use time::OffsetDateTime;
use uuid::Uuid;

pub const DEVICE_GRAPH_SCHEMA_VERSION: &str = "1.0.0";

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct DeviceGraph {
    pub schema_version: String,
    pub graph_id: Uuid,
    pub generated_at_utc: String,
    pub host: HostInfo,
    pub disks: Vec<Disk>,
}

impl DeviceGraph {
    pub fn new(host: HostInfo, disks: Vec<Disk>, generated_at_utc: String) -> Self {
        Self {
            schema_version: DEVICE_GRAPH_SCHEMA_VERSION.to_string(),
            graph_id: Uuid::new_v4(),
            generated_at_utc,
            host,
            disks,
        }
    }
}

pub fn now_utc_rfc3339() -> String {
    OffsetDateTime::now_utc()
        .format(&Rfc3339)
        .unwrap_or_else(|_| "unknown".to_string())
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
    pub removable: bool,
    pub is_system_disk: bool,      // provider best-effort
    pub volumes: Vec<Volume>,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct Volume {
    pub id: String,
    pub label: Option<String>,
    pub fs: Option<String>,
    pub size_bytes: u64,
    pub mount_points: Vec<String>,
}
