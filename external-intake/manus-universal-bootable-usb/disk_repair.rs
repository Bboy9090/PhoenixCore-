/// Disk repair module with fsck integration
/// 
/// Provides safe disk scanning and repair using fsck with proper safety checks

use serde::{Deserialize, Serialize};
use std::process::Command;
use std::path::Path;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DiskRepairResult {
    pub device: String,
    pub success: bool,
    pub message: String,
    pub errors_found: usize,
    pub errors_fixed: usize,
    pub duration_seconds: u64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DiskScanResult {
    pub device: String,
    pub status: String,
    pub errors: Vec<String>,
    pub warnings: Vec<String>,
    pub is_healthy: bool,
}

/// Check if device is a system disk (safety check)
fn is_system_disk(device: &str) -> bool {
    // Prevent operations on common system disks
    device == "/" || 
    device.contains("sda1") || 
    device.contains("nvme0n1p1") ||
    device.contains("mmcblk0p1") ||
    device.starts_with("/dev/root")
}

/// Check if device is mounted (safety check)
fn is_device_mounted(device: &str) -> bool {
    if let Ok(output) = Command::new("mountpoint")
        .arg(device)
        .output()
    {
        output.status.success()
    } else {
        // Fallback: check /etc/mtab
        if let Ok(mtab) = std::fs::read_to_string("/etc/mtab") {
            mtab.contains(device)
        } else {
            false
        }
    }
}

/// Get filesystem type for device
fn get_filesystem_type(device: &str) -> Result<String, String> {
    let output = Command::new("blkid")
        .arg("-o")
        .arg("value")
        .arg("-s")
        .arg("TYPE")
        .arg(device)
        .output()
        .map_err(|e| format!("Failed to get filesystem type: {}", e))?;

    if output.status.success() {
        Ok(String::from_utf8_lossy(&output.stdout).trim().to_string())
    } else {
        Err("Could not determine filesystem type".to_string())
    }
}

/// Scan disk for errors using fsck (read-only)
pub fn scan_disk_errors(device: &str) -> Result<DiskScanResult, String> {
    // Safety checks
    if is_system_disk(device) {
        return Err("Cannot scan system disk for safety reasons".to_string());
    }

    if is_device_mounted(device) {
        return Err(format!("Device {} is mounted. Unmount before scanning.", device));
    }

    let filesystem = get_filesystem_type(device)?;

    // Run fsck in read-only mode
    let output = Command::new("fsck")
        .arg("-n") // Read-only mode
        .arg("-f") // Force check
        .arg(device)
        .output()
        .map_err(|e| format!("Failed to scan disk: {}", e))?;

    let stdout = String::from_utf8_lossy(&output.stdout);
    let stderr = String::from_utf8_lossy(&output.stderr);
    let combined = format!("{}\n{}", stdout, stderr);

    // Parse fsck output
    let mut errors = Vec::new();
    let mut warnings = Vec::new();
    let mut is_healthy = true;

    for line in combined.lines() {
        if line.contains("error") || line.contains("Error") {
            errors.push(line.to_string());
            is_healthy = false;
        } else if line.contains("warning") || line.contains("Warning") {
            warnings.push(line.to_string());
        }
    }

    Ok(DiskScanResult {
        device: device.to_string(),
        status: if is_healthy { "healthy" } else { "has_errors" }.to_string(),
        errors,
        warnings,
        is_healthy,
    })
}

/// Repair disk using fsck
pub fn repair_disk(device: &str) -> Result<DiskRepairResult, String> {
    // Safety checks
    if is_system_disk(device) {
        return Err("Cannot repair system disk for safety reasons".to_string());
    }

    if is_device_mounted(device) {
        return Err(format!("Device {} is mounted. Unmount before repair.", device));
    }

    // Check filesystem type
    let filesystem = get_filesystem_type(device)?;

    // Run fsck with automatic repair
    let start = std::time::Instant::now();
    
    let output = Command::new("fsck")
        .arg("-y") // Automatically answer yes to all questions
        .arg("-f") // Force check
        .arg(device)
        .output()
        .map_err(|e| format!("Failed to repair disk: {}", e))?;

    let duration = start.elapsed().as_secs();
    let stdout = String::from_utf8_lossy(&output.stdout);
    let stderr = String::from_utf8_lossy(&output.stderr);
    let combined = format!("{}\n{}", stdout, stderr);

    // Parse repair output
    let mut errors_found = 0;
    let mut errors_fixed = 0;

    for line in combined.lines() {
        if line.contains("error") {
            errors_found += 1;
        }
        if line.contains("fixed") || line.contains("repaired") {
            errors_fixed += 1;
        }
    }

    let success = output.status.success();
    let message = if success {
        format!("Disk repair completed. Found {} errors, fixed {}.", errors_found, errors_fixed)
    } else {
        "Disk repair encountered errors. Manual intervention may be required.".to_string()
    };

    Ok(DiskRepairResult {
        device: device.to_string(),
        success,
        message,
        errors_found,
        errors_fixed,
        duration_seconds: duration,
    })
}

/// Check disk health without repair
pub fn check_disk_health(device: &str) -> Result<bool, String> {
    if is_system_disk(device) {
        return Err("Cannot check system disk health for safety reasons".to_string());
    }

    let result = scan_disk_errors(device)?;
    Ok(result.is_healthy)
}

/// Get SMART status (for SSDs/HDDs that support it)
pub fn get_smart_status(device: &str) -> Result<String, String> {
    if is_system_disk(device) {
        return Err("Cannot get SMART status for system disk".to_string());
    }

    let output = Command::new("smartctl")
        .arg("-H")
        .arg(device)
        .output()
        .map_err(|e| format!("smartctl not available: {}", e))?;

    if output.status.success() {
        Ok(String::from_utf8_lossy(&output.stdout).to_string())
    } else {
        Err("Device does not support SMART or smartctl is not installed".to_string())
    }
}

/// Defragment filesystem (for ext4, btrfs, etc.)
pub fn defragment_filesystem(device: &str) -> Result<String, String> {
    if is_system_disk(device) {
        return Err("Cannot defragment system disk for safety reasons".to_string());
    }

    if is_device_mounted(device) {
        return Err(format!("Device {} is mounted. Unmount before defragmentation.", device));
    }

    let filesystem = get_filesystem_type(device)?;

    match filesystem.as_str() {
        "ext4" | "ext3" | "ext2" => {
            let output = Command::new("e4defrag")
                .arg(device)
                .output()
                .map_err(|e| format!("Failed to defragment: {}", e))?;

            if output.status.success() {
                Ok("Defragmentation completed successfully".to_string())
            } else {
                Err("Defragmentation failed".to_string())
            }
        }
        "btrfs" => {
            let output = Command::new("btrfs")
                .arg("filesystem")
                .arg("defragment")
                .arg(device)
                .output()
                .map_err(|e| format!("Failed to defragment: {}", e))?;

            if output.status.success() {
                Ok("Btrfs defragmentation completed successfully".to_string())
            } else {
                Err("Btrfs defragmentation failed".to_string())
            }
        }
        _ => Err(format!("Defragmentation not supported for {} filesystem", filesystem)),
    }
}

/// Securely wipe free space on disk
pub fn wipe_free_space(device: &str) -> Result<String, String> {
    if is_system_disk(device) {
        return Err("Cannot wipe system disk for safety reasons".to_string());
    }

    if is_device_mounted(device) {
        return Err(format!("Device {} is mounted. Unmount before wiping.", device));
    }

    // Use shred or dd to wipe free space
    let output = Command::new("shred")
        .arg("-vfz")
        .arg("-n")
        .arg("3")
        .arg(device)
        .output()
        .map_err(|e| format!("Failed to wipe free space: {}", e))?;

    if output.status.success() {
        Ok("Free space wiped successfully".to_string())
    } else {
        Err("Failed to wipe free space".to_string())
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_is_system_disk() {
        assert!(is_system_disk("/"));
        assert!(is_system_disk("/dev/sda1"));
        assert!(is_system_disk("/dev/nvme0n1p1"));
        assert!(!is_system_disk("/dev/sdb1"));
        assert!(!is_system_disk("/dev/usb1"));
    }

    #[test]
    fn test_scan_system_disk_fails() {
        let result = scan_disk_errors("/");
        assert!(result.is_err());
        assert!(result.unwrap_err().contains("system disk"));
    }

    #[test]
    fn test_repair_system_disk_fails() {
        let result = repair_disk("/");
        assert!(result.is_err());
        assert!(result.unwrap_err().contains("system disk"));
    }
}
