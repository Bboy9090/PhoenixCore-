use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use uuid::Uuid;

pub mod capability;
pub mod dashboard;
pub mod downloader;
pub mod orchestrator;
pub mod rescue;

pub const WORKFLOW_SCHEMA_VERSION: &str = "1.0.0";

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct DeviceGraph {
    pub schema_version: String,
    pub run_id: Uuid,
    pub timestamp: DateTime<Utc>,
    pub generated_at_utc: String,
    pub host_info: HostInfo,
    pub host: HostInfo,
    pub disks: Vec<Disk>,
}

impl Default for DeviceGraph {
    fn default() -> Self {
        let timestamp = Utc::now();
        let generated_at_utc = timestamp.to_rfc3339();
        let host = HostInfo::default();
        Self {
            schema_version: "1.0.0".to_string(),
            run_id: Uuid::new_v4(),
            timestamp,
            generated_at_utc,
            host_info: host.clone(),
            host,
            disks: Vec::new(),
        }
    }
}

impl DeviceGraph {
    pub fn new(host: HostInfo, disks: Vec<Disk>, generated_at_utc: String) -> Self {
        Self {
            schema_version: "1.0.0".to_string(),
            run_id: Uuid::new_v4(),
            timestamp: Utc::now(),
            generated_at_utc,
            host_info: host.clone(),
            host,
            disks,
        }
    }

    pub fn to_json(&self, pretty: bool) -> Result<String, serde_json::Error> {
        if pretty {
            serde_json::to_string_pretty(self)
        } else {
            serde_json::to_string(self)
        }
    }
}

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct HostInfo {
    pub hostname: String,
    pub os: String,
    pub arch: String,
    pub kernel_version: String,
    pub os_version: String,
    pub machine: String,
}

impl Default for HostInfo {
    fn default() -> Self {
        Self {
            hostname: String::new(),
            os: String::new(),
            arch: String::new(),
            kernel_version: String::new(),
            os_version: String::new(),
            machine: String::new(),
        }
    }
}

impl HostInfo {
    pub fn new(os: impl Into<String>, os_version: impl Into<String>, machine: impl Into<String>) -> Self {
        let machine = machine.into();
        Self {
            hostname: machine.clone(),
            os: os.into(),
            arch: std::env::consts::ARCH.to_string(),
            kernel_version: String::new(),
            os_version: os_version.into(),
            machine,
        }
    }
}

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct Disk {
    pub id: String,
    pub friendly_name: Option<String>,
    pub size_bytes: u64,
    pub removable: bool,
    pub is_system_disk: bool,
    pub volumes: Vec<Volume>,
    pub partitions: Vec<Partition>,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct Volume {
    pub id: String,
    pub label: Option<String>,
    pub filesystem: Option<String>,
    pub size_bytes: u64,
    pub mount_points: Vec<String>,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct Partition {
    pub id: String,
    pub label: Option<String>,
    pub fs: Option<String>,
    pub size_bytes: u64,
    pub mount_points: Vec<String>,
}

impl From<&Partition> for Volume {
    fn from(partition: &Partition) -> Self {
        Self {
            id: partition.id.clone(),
            label: partition.label.clone(),
            filesystem: partition.fs.clone(),
            size_bytes: partition.size_bytes,
            mount_points: partition.mount_points.clone(),
        }
    }
}

impl From<&Volume> for Partition {
    fn from(volume: &Volume) -> Self {
        Self {
            id: volume.id.clone(),
            label: volume.label.clone(),
            fs: volume.filesystem.clone(),
            size_bytes: volume.size_bytes,
            mount_points: volume.mount_points.clone(),
        }
    }
}

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct RunReport {
    pub run_id: Uuid,
    pub timestamp: DateTime<Utc>,
    pub status: String,
    pub message: String,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct WorkflowDefinition {
    pub schema_version: String,
    pub name: String,
    pub steps: Vec<WorkflowStep>,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct WorkflowStep {
    pub id: String,
    pub action: String,
    #[serde(default)]
    pub params: serde_json::Value,
}

pub fn now_utc_rfc3339() -> String {
    Utc::now().to_rfc3339()
}
