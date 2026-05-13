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

pub const WORKFLOW_SCHEMA_VERSION: &str = "1.0";

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct WorkflowStep {
    pub id: String,
    pub name: String,
    pub action: String,
    pub params: serde_json::Value,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct WorkflowDefinition {
    pub id: String,
    pub name: String,
    pub schema_version: String,
    pub steps: Vec<WorkflowStep>,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct Disk {
    pub id: String,
    pub friendly_name: String,
    pub size_bytes: u64,
    pub removable: bool,
    pub is_system_disk: bool,
    pub volumes: Vec<Volume>,
    #[serde(default)]
    pub partitions: Vec<Volume>,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct Volume {
    pub id: String,
    pub label: Option<String>,
    pub size_bytes: u64,
    pub mount_points: Vec<String>,
    pub fs: Option<String>,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct RunReport {
    pub run_id: Uuid,
    pub timestamp: DateTime<Utc>,
    pub status: String,
    pub message: String,
}

pub type Partition = Volume;

pub fn now_utc_rfc3339() -> String {
    Utc::now().to_rfc3339()
}

impl DeviceGraph {
    pub fn new(host_info: HostInfo, disks: Vec<Disk>, _timestamp: String) -> Self {
        Self {
            schema_version: "1.0.0".to_string(),
            run_id: Uuid::new_v4(),
            timestamp: Utc::now(),
            host_info,
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
