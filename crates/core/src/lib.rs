use serde::{Deserialize, Serialize};
use serde_json::Value;
use time::format_description::well_known::Rfc3339;
use time::OffsetDateTime;
use uuid::Uuid;

pub const DEVICE_GRAPH_SCHEMA_VERSION: &str = "1.1.0";
pub const WORKFLOW_SCHEMA_VERSION: &str = "1.0.0";
pub const CONTRACTS_VERSION: &str = "1.0.0";

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
    pub params: Value,
}

impl WorkflowDefinition {
    pub fn new(name: impl Into<String>, steps: Vec<WorkflowStep>) -> Self {
        Self {
            schema_version: WORKFLOW_SCHEMA_VERSION.to_string(),
            name: name.into(),
            steps,
        }
    }
}

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct CoreError {
    pub message: String,
}

impl CoreError {
    pub fn new(message: impl Into<String>) -> Self {
        Self {
            message: message.into(),
        }
    }
}

pub type CoreResult<T> = std::result::Result<T, CoreError>;

pub trait HostProvider {
    fn device_graph(&self) -> CoreResult<DeviceGraph>;
}

pub trait ImagingProvider {
    type Reader;

    fn open_read_only(&self, disk_id: &str) -> CoreResult<Self::Reader>;
    fn read_exact(&self, reader: &mut Self::Reader, offset: u64, length: u64)
        -> CoreResult<Vec<u8>>;
}
