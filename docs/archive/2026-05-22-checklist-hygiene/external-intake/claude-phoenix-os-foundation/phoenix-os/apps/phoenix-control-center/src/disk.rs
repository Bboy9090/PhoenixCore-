// Phoenix OS — Phoenix Control Center: Disk Module
// File: apps/phoenix-control-center/src/disk.rs
//
// Provides disk enumeration and S.M.A.R.T. data retrieval.
// All disk operations are read-only — this module NEVER writes to disks.
//
// SAFETY: This module implements the Phoenix disk safety model:
//   - Only reads disk metadata
//   - Never auto-selects a disk for any operation
//   - Destructive operations are NOT in this module (see phoenix-recovery)

use serde::{Deserialize, Serialize};
use std::process::Command;

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct DiskInfo {
    pub device: String,
    pub model: String,
    pub serial: String,
    pub size_bytes: u64,
    pub size_human: String,
    pub bus_type: String, // "sata", "nvme", "usb", "unknown"
    pub partitions: Vec<PartitionInfo>,
    pub smart_available: bool,
    pub health_status: DiskHealth,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct PartitionInfo {
    pub device: String,
    pub size_bytes: u64,
    pub size_human: String,
    pub filesystem: Option<String>,
    pub mountpoint: Option<String>,
    pub label: Option<String>,
    pub uuid: Option<String>,
}

#[derive(Debug, Serialize, Deserialize, Clone, PartialEq)]
pub enum DiskHealth {
    Passed,
    Warning,
    Failed,
    Unknown,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct SmartData {
    pub device: String,
    pub overall_health: DiskHealth,
    pub temperature_celsius: Option<i32>,
    pub power_on_hours: Option<u64>,
    pub reallocated_sectors: Option<u64>,
    pub pending_sectors: Option<u64>,
    pub uncorrectable_errors: Option<u64>,
    pub attributes: Vec<SmartAttribute>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct SmartAttribute {
    pub id: u8,
    pub name: String,
    pub value: u64,
    pub worst: u64,
    pub threshold: u64,
    pub raw_value: u64,
    pub status: AttributeStatus,
}

#[derive(Debug, Serialize, Deserialize)]
pub enum AttributeStatus {
    Ok,
    Warning,
    Critical,
}

/// List all block devices using lsblk JSON output.
/// Returns only physical disks (not loop devices, not the live boot media).
#[tauri::command]
pub fn list_disks() -> Result<Vec<DiskInfo>, String> {
    let output = Command::new("lsblk")
        .args([
            "--json",
            "--output",
            "NAME,SIZE,MODEL,SERIAL,TRAN,TYPE,FSTYPE,MOUNTPOINT,LABEL,UUID,PHY-SEC",
            "--bytes",
            "--exclude",
            "7", // Exclude loop devices (type 7)
        ])
        .output()
        .map_err(|e| format!("Failed to run lsblk: {}", e))?;

    if !output.status.success() {
        return Err(format!(
            "lsblk failed: {}",
            String::from_utf8_lossy(&output.stderr)
        ));
    }

    // TODO: Parse lsblk JSON output into Vec<DiskInfo>
    // The JSON structure from lsblk --json is:
    // { "blockdevices": [ { "name": "sda", "size": "...", "children": [...] } ] }
    // Implementation placeholder — full parser in Phase 1

    let _json_output = String::from_utf8_lossy(&output.stdout);

    // Stub: return empty list until parser is implemented
    Ok(vec![])
}

/// Get S.M.A.R.T. data for a specific device.
/// Requires: smartmontools (smartctl)
/// Privilege: requires sudo/polkit (smartctl needs elevated access)
#[tauri::command]
pub fn get_disk_smart(device: String) -> Result<SmartData, String> {
    // Validate device path to prevent injection
    if !device.starts_with("/dev/") {
        return Err(format!("Invalid device path: {}", device));
    }

    // Additional validation: device must exist
    if !std::path::Path::new(&device).exists() {
        return Err(format!("Device does not exist: {}", device));
    }

    // TODO: Invoke smartctl via polkit-authorized helper
    // For now, return an Unknown health stub
    // Full implementation in Phase 1

    Ok(SmartData {
        device: device.clone(),
        overall_health: DiskHealth::Unknown,
        temperature_celsius: None,
        power_on_hours: None,
        reallocated_sectors: None,
        pending_sectors: None,
        uncorrectable_errors: None,
        attributes: vec![],
    })
}

/// Get basic disk information (non-S.M.A.R.T.) for a device.
#[tauri::command]
pub fn get_disk_info(device: String) -> Result<DiskInfo, String> {
    // Validate device path
    if !device.starts_with("/dev/") {
        return Err(format!("Invalid device path: {}", device));
    }

    // TODO: Implement using lsblk, udevadm, hdparm -I for detailed info
    // Stub implementation for Phase 0

    Ok(DiskInfo {
        device: device.clone(),
        model: "Unknown".to_string(),
        serial: "Unknown".to_string(),
        size_bytes: 0,
        size_human: "Unknown".to_string(),
        bus_type: "unknown".to_string(),
        partitions: vec![],
        smart_available: false,
        health_status: DiskHealth::Unknown,
    })
}
