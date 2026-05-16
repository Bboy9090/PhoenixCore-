#[cfg(windows)]
pub mod format;
#[cfg(not(windows))]
#[path = "format_stub.rs"]
pub mod format;

#[cfg(windows)]
pub mod space;
#[cfg(not(windows))]
#[path = "space_stub.rs"]
pub mod space;

use anyhow::Result;
use phoenix_core::{DeviceGraph, Disk, HostInfo, Partition, Volume};

pub fn build_device_graph() -> Result<DeviceGraph> {
    Ok(DeviceGraph::new(
        get_host_info()?,
        get_disks()?,
        phoenix_core::now_utc_rfc3339(),
    ))
}

#[cfg(windows)]
fn get_host_info() -> Result<HostInfo> {
    Ok(HostInfo {
        hostname: "Windows-Host".to_string(), // Placeholder for now
        os: "Windows".to_string(),
        arch: std::env::consts::ARCH.to_string(),
        kernel_version: "unknown".to_string(),
        os_version: "unknown".to_string(),
        machine: "Windows-Host".to_string(),
    })
}

#[cfg(not(windows))]
fn get_host_info() -> Result<HostInfo> {
    Ok(HostInfo {
        hostname: "Non-Windows-Stub".to_string(),
        os: std::env::consts::OS.to_string(),
        arch: std::env::consts::ARCH.to_string(),
        kernel_version: "stub".to_string(),
        os_version: "stub".to_string(),
        machine: "Non-Windows-Stub".to_string(),
    })
}

#[cfg(windows)]
fn get_disks() -> Result<Vec<Disk>> {
    // Real implementation would iterate PhysicalDrive0..N
    // This is a placeholder that identifies the structure for Pass B
    let mut disks = Vec::new();

    // Sample "System Disk" logic
    let volumes = vec![Volume {
        id: "C:".to_string(),
        label: Some("OS".to_string()),
        filesystem: Some("NTFS".to_string()),
        size_bytes: 400 * 1024 * 1024 * 1024,
        mount_points: vec!["C:".to_string()],
    }];
    let partitions = volumes.iter().map(Partition::from).collect();
    disks.push(Disk {
        id: "\\\\.\\PhysicalDrive0".to_string(),
        friendly_name: Some("System SSD".to_string()),
        size_bytes: 512 * 1024 * 1024 * 1024, // 512GB
        removable: false,
        is_system_disk: true,
        volumes,
        partitions,
    });

    Ok(disks)
}

#[cfg(not(windows))]
fn get_disks() -> Result<Vec<Disk>> {
    // Stub for non-windows to allow compilation
    Ok(vec![{
        let volumes = vec![Volume {
            id: "/".to_string(),
            label: Some("Macintosh HD".to_string()),
            filesystem: Some("APFS".to_string()),
            size_bytes: 200 * 1024 * 1024 * 1024,
            mount_points: vec!["/".to_string()],
        }];
        let partitions = volumes.iter().map(Partition::from).collect();
        Disk {
            id: "/dev/disk0".to_string(),
            friendly_name: Some("Macintosh HD Stub".to_string()),
            size_bytes: 250 * 1024 * 1024 * 1024,
            removable: false,
            is_system_disk: true,
            volumes,
            partitions,
        }
    }])
}
