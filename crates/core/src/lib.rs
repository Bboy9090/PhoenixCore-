use serde::{Deserialize, Serialize};
use time::format_description::well_known::Rfc3339;
use uuid::Uuid;

pub const DEVICE_GRAPH_SCHEMA_VERSION: &str = "1.0.0";
pub const WORKFLOW_SCHEMA_VERSION: &str = "1.0.0";

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct DeviceGraph {
    pub graph_id: Uuid,
    pub schema_version: String,
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
    pub params: serde_json::Value,
}

impl DeviceGraph {
    pub fn new(host: HostInfo, disks: Vec<Disk>) -> Self {
        Self {
            graph_id: Uuid::new_v4(),
            schema_version: DEVICE_GRAPH_SCHEMA_VERSION.to_string(),
            host,
            disks,
            generated_at_utc: now_utc_rfc3339(),
        }
    }
}

pub fn now_utc_rfc3339() -> String {
    time::OffsetDateTime::now_utc()
        .format(&Rfc3339)
        .unwrap_or_else(|_| "1970-01-01T00:00:00Z".to_string())
}
