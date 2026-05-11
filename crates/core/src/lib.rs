use serde::{Deserialize, Serialize};
use chrono::{DateTime, Utc};
use uuid::Uuid;

pub mod rescue;
pub mod capability;
pub mod orchestrator;
pub mod downloader;

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct DeviceGraph {
    pub schema_version: String,
    pub run_id: Uuid,
    pub timestamp: DateTime<Utc>,
    pub host_info: HostInfo,
    pub disks: Vec<Disk>,
}

impl Default for DeviceGraph {
    fn default() -> Self {
        Self {
            schema_version: "1.0.0".to_string(),
            run_id: Uuid::new_v4(),
            timestamp: Utc::now(),
            host_info: HostInfo::default(),
            disks: Vec::new(),
        }
    }
}

#[derive(Debug, Serialize, Deserialize, Clone, Default)]
pub struct HostInfo {
    pub hostname: String,
    pub os: String,
    pub arch: String,
    pub kernel_version: String,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct Disk {
    pub id: String, // e.g. \\.\PhysicalDrive0
    pub friendly_name: Option<String>,
    pub size_bytes: u64,
    pub removable: bool,
    pub is_system_disk: bool,
    pub volumes: Vec<Volume>,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct Volume {
    pub id: String, // Stable ID if possible
    pub label: Option<String>,
    pub filesystem: Option<String>,
    pub size_bytes: u64,
    pub mount_points: Vec<String>, // Drive letters on Windows
}

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct RunReport {
    pub run_id: Uuid,
    pub timestamp: DateTime<Utc>,
    pub status: String,
    pub message: String,
}

impl DeviceGraph {
    pub fn to_json(&self, pretty: bool) -> Result<String, serde_json::Error> {
        if pretty {
            serde_json::to_string_pretty(self)
        } else {
            serde_json::to_string(self)
        }
    }
}
