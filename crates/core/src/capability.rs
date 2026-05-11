use serde::{Deserialize, Serialize};
use std::collections::HashMap;

#[derive(Debug, Serialize, Deserialize, Clone, PartialEq, Eq, Hash)]
pub enum ActionId {
    RefreshDetect,
    GetDeviceInfo,
    RebootToRecovery,
    ExitRecovery,
    ExportLogs,
    RepairPairing,
    PwnDevice,
    BackupDevice,
    ImageRestore,
}

#[derive(Debug, Serialize, Deserialize, Clone, PartialEq, Eq, Hash)]
pub enum DeviceState {
    Normal,
    Recovery,
    Dfu,
    AdbMode,
    FastbootMode,
    Unknown,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct ActionCapability {
    pub allowed_states: Vec<DeviceState>,
    pub requires_high_integrity: bool,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct ImagingJob {
    pub job_id: String,
    pub target_disk: String,
    pub expected_size_bytes: u64,
    pub expected_serial: Option<String>,
    pub image_path: String,
    pub mode: String,
    pub verify: bool,
}

pub struct CapabilityMatrix {
    pub matrix: HashMap<ActionId, ActionCapability>,
}

impl Default for CapabilityMatrix {
    fn default() -> Self {
        let mut matrix = HashMap::new();
        // Register ImageRestore as a high-integrity gated action
        matrix.insert(ActionId::ImageRestore, ActionCapability {
            allowed_states: vec![DeviceState::Normal, DeviceState::Recovery, DeviceState::Dfu],
            requires_high_integrity: true,
        });
        Self { matrix }
    }
}

impl CapabilityMatrix {
    /// Performs a high-integrity gate check for a specific job
    pub fn enforce_gate(&self, job: &ImagingJob, current_state: &DeviceState, actual_disk_size: u64) -> Result<()> {
        // 1. Action Authorization
        let action = ActionId::ImageRestore;
        if !self.can_execute(&action, current_state) {
            return Err(anyhow::anyhow!("CAPABILITY_DENIED: Device state {:?} not authorized for imaging.", current_state));
        }

        // 2. Hardware Fingerprint Verification (Anti-Targeting Risk)
        if actual_disk_size != job.expected_size_bytes {
            return Err(anyhow::anyhow!(
                "FINGERPRINT_MISMATCH: Target disk size ({} bytes) does not match job manifest ({} bytes).",
                actual_disk_size, job.expected_size_bytes
            ));
        }

        // 3. Path Validation
        if !job.target_disk.starts_with("/dev/disk") && !job.target_disk.starts_with(r"\\.\") {
             return Err(anyhow::anyhow!("SECURITY_VIOLATION: Unauthorized disk path format: {}", job.target_disk));
        }

        Ok(())
    }

    pub fn can_execute(&self, action: &ActionId, current_state: &DeviceState) -> bool {
        if let Some(cap) = self.matrix.get(action) {
            cap.allowed_states.contains(current_state)
        } else {
            false
        }
    }
}
