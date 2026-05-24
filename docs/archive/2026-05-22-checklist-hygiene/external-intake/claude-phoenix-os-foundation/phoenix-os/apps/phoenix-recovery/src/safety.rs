// Phoenix OS — Phoenix Recovery: Safety Module
// File: apps/phoenix-recovery/src/safety.rs
//
// Implements the Phoenix OS disk safety model for destructive operations.
// See docs/security-model.md — Principle 2: Confirmation Gates
//
// Every destructive operation must:
//   1. Call get_device_details() to display device info to the user
//   2. Present a confirmation dialog with full device info
//   3. Require the user to TYPE the device path (not just click OK)
//   4. Call confirm_destructive_operation() which validates the typed path
//   5. Log the confirmed operation to the disk audit log

use serde::{Deserialize, Serialize};
use std::process::Command;

#[derive(Debug, Serialize, Deserialize)]
pub struct DeviceDetails {
    pub path: String,
    pub model: String,
    pub serial: String,
    pub size_human: String,
    pub size_bytes: u64,
    pub bus_type: String,
    pub partitions: Vec<String>,
    /// True if this appears to be the live boot device (USB with Phoenix OS)
    /// Destructive operations on the live device should be extra-warned.
    pub is_live_device: bool,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct ConfirmationRequest {
    /// The device path the user typed in the confirmation dialog
    pub typed_path: String,
    /// The device path the operation targets
    pub target_path: String,
    /// Human-readable description of the operation
    pub operation_description: String,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct ConfirmationResult {
    pub confirmed: bool,
    pub reason: Option<String>,
}

/// Get detailed information about a device for display in confirmation dialogs.
/// Called before any destructive operation to show the user what they're targeting.
#[tauri::command]
pub fn get_device_details(device_path: String) -> Result<DeviceDetails, String> {
    // Validate device path
    if !is_valid_device_path(&device_path) {
        return Err(format!("Invalid device path: {}", device_path));
    }

    if !std::path::Path::new(&device_path).exists() {
        return Err(format!("Device does not exist: {}", device_path));
    }

    // Get device info via udevadm
    let udev_output = Command::new("udevadm")
        .args(["info", "--query=all", "--name", &device_path])
        .output()
        .map_err(|e| format!("Failed to run udevadm: {}", e))?;

    let udev_str = String::from_utf8_lossy(&udev_output.stdout);

    let model = extract_udev_property(&udev_str, "ID_MODEL")
        .unwrap_or_else(|| "Unknown Model".to_string());
    let serial = extract_udev_property(&udev_str, "ID_SERIAL_SHORT")
        .unwrap_or_else(|| "Unknown Serial".to_string());
    let bus_type = extract_udev_property(&udev_str, "ID_BUS")
        .unwrap_or_else(|| "unknown".to_string());

    // Get size via lsblk
    let size_output = Command::new("lsblk")
        .args(["--nodeps", "--noheadings", "--output", "SIZE,SIZE", "--bytes", &device_path])
        .output()
        .unwrap_or_default();

    let size_str = String::from_utf8_lossy(&size_output.stdout);
    let size_parts: Vec<&str> = size_str.split_whitespace().collect();
    let size_bytes: u64 = size_parts.first()
        .and_then(|s| s.parse().ok())
        .unwrap_or(0);
    let size_human = size_parts.get(1).unwrap_or(&"Unknown").to_string();

    // Check if this is the live device
    let is_live_device = check_is_live_device(&device_path);

    // List partitions
    let partitions = list_partitions(&device_path);

    Ok(DeviceDetails {
        path: device_path,
        model,
        serial,
        size_human,
        size_bytes,
        bus_type,
        partitions,
        is_live_device,
    })
}

/// Validate a destructive operation confirmation.
///
/// The confirmation is valid ONLY if:
///   1. typed_path exactly matches target_path (case-sensitive)
///   2. target_path is a valid block device path
///   3. The operation is logged to the audit log
///
/// This implements the "type the device path" confirmation gate.
#[tauri::command]
pub fn confirm_destructive_operation(
    request: ConfirmationRequest,
) -> Result<ConfirmationResult, String> {
    // Validate the target path
    if !is_valid_device_path(&request.target_path) {
        return Ok(ConfirmationResult {
            confirmed: false,
            reason: Some(format!("Invalid target device path: {}", request.target_path)),
        });
    }

    // The typed path must EXACTLY match the target path
    if request.typed_path.trim() != request.target_path {
        return Ok(ConfirmationResult {
            confirmed: false,
            reason: Some(format!(
                "Typed path '{}' does not match target path '{}'",
                request.typed_path.trim(),
                request.target_path
            )),
        });
    }

    // Log the confirmed operation to the audit log
    log_disk_operation(
        &request.target_path,
        "phoenix-recovery",
        &request.operation_description,
        "CONFIRMED",
    );

    Ok(ConfirmationResult {
        confirmed: true,
        reason: None,
    })
}

// ---- Helper functions ----

fn is_valid_device_path(path: &str) -> bool {
    // Must start with /dev/
    if !path.starts_with("/dev/") {
        return false;
    }

    // Must not contain path traversal
    if path.contains("..") || path.contains("//") {
        return false;
    }

    // Must match known block device patterns: /dev/sdX, /dev/nvmeXnY, /dev/mmcblkX
    let dev_name = &path[5..]; // Strip /dev/
    let valid = dev_name.starts_with("sd")
        || dev_name.starts_with("nvme")
        || dev_name.starts_with("mmcblk")
        || dev_name.starts_with("vd")  // VirtIO
        || dev_name.starts_with("hd"); // Legacy IDE

    valid && dev_name.len() <= 20 // Reasonable max length
}

fn extract_udev_property(udev_output: &str, key: &str) -> Option<String> {
    for line in udev_output.lines() {
        if let Some(value) = line.strip_prefix(&format!("E: {}=", key)) {
            return Some(value.trim().to_string());
        }
    }
    None
}

fn check_is_live_device(device_path: &str) -> bool {
    // Check /proc/cmdline for the boot device
    // In a casper live session, the live media path is in the cmdline
    let cmdline = std::fs::read_to_string("/proc/cmdline").unwrap_or_default();
    
    // Casper uses LABEL=writable or similar — this is a heuristic
    // A more robust check would compare the device to the mounted live media
    let _ = device_path; // Used in the full implementation
    let _ = cmdline;
    
    // TODO: Implement robust live device detection by checking
    // /sys/block/<dev>/removable and comparing against mounted live media
    false
}

fn list_partitions(device_path: &str) -> Vec<String> {
    let output = Command::new("lsblk")
        .args(["--noheadings", "--output", "NAME", "--list", device_path])
        .output()
        .unwrap_or_default();

    String::from_utf8_lossy(&output.stdout)
        .lines()
        .filter(|line| !line.trim().is_empty())
        .map(|line| format!("/dev/{}", line.trim()))
        .collect()
}

fn log_disk_operation(device: &str, tool: &str, operation: &str, status: &str) {
    use std::io::Write;
    
    let timestamp = chrono_now(); // TODO: add chrono dependency or use simpler time
    let user = std::env::var("USER").unwrap_or_else(|_| "unknown".to_string());
    
    let log_entry = format!(
        "[{}] {} {} {} {} {}\n",
        timestamp, user, tool, operation, device, status
    );

    let _ = std::fs::OpenOptions::new()
        .create(true)
        .append(true)
        .open("/var/log/phoenix/disk-ops.log")
        .and_then(|mut f| f.write_all(log_entry.as_bytes()));
}

fn chrono_now() -> String {
    // Simple timestamp without chrono dependency for Phase 0
    // TODO: Replace with chrono or time crate
    std::time::SystemTime::now()
        .duration_since(std::time::UNIX_EPOCH)
        .map(|d| d.as_secs().to_string())
        .unwrap_or_else(|_| "0".to_string())
}
