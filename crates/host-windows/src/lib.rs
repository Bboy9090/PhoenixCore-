use phoenix_core::{DeviceGraph, Disk, Volume, HostInfo};
use anyhow::Result;

pub fn build_device_graph() -> Result<DeviceGraph> {
    let mut graph = DeviceGraph::default();
    
    // Host Info
    graph.host_info = get_host_info()?;
    
    // Disks & Volumes
    graph.disks = get_disks()?;
    
    Ok(graph)
}

#[cfg(windows)]
fn get_host_info() -> Result<HostInfo> {
    // use windows::Win32::System::SystemInformation::{GetComputerNameW, GetSystemInfo};
    // ... Windows implementation ...
    Ok(HostInfo {
        hostname: "Windows-Host".to_string(), // Placeholder for now
        os: "Windows".to_string(),
        arch: std::env::consts::ARCH.to_string(),
        kernel_version: "unknown".to_string(),
    })
}

#[cfg(not(windows))]
fn get_host_info() -> Result<HostInfo> {
    Ok(HostInfo {
        hostname: "Non-Windows-Stub".to_string(),
        os: std::env::consts::OS.to_string(),
        arch: std::env::consts::ARCH.to_string(),
        kernel_version: "stub".to_string(),
    })
}

#[cfg(windows)]
fn get_disks() -> Result<Vec<Disk>> {
    // use windows::Win32::Storage::FileSystem::{GetLogicalDrives, GetVolumeInformationW, GetDriveTypeW};
    // use windows::Win32::Foundation::HANDLE;
    // Real implementation would iterate PhysicalDrive0..N
    // This is a placeholder that identifies the structure for Pass B
    let mut disks = Vec::new();
    
    // Sample "System Disk" logic
    let volumes = vec![
        Volume {
            id: "C:".to_string(),
            label: Some("OS".to_string()),
            fs: Some("NTFS".to_string()),
            size_bytes: 400 * 1024 * 1024 * 1024,
            mount_points: vec!["C:".to_string()],
        }
    ];

    disks.push(Disk {
        id: "\\\\.\\PhysicalDrive0".to_string(),
        friendly_name: "System SSD".to_string(),
        size_bytes: 512 * 1024 * 1024 * 1024, // 512GB
        removable: false,
        is_system_disk: true,
        volumes: volumes.clone(),
        partitions: volumes,
    });

    Ok(disks)
}

#[cfg(not(windows))]
fn get_disks() -> Result<Vec<Disk>> {
    // Stub for non-windows to allow compilation
    Ok(vec![
        Disk {
            id: "/dev/disk0".to_string(),
            friendly_name: Some("Macintosh HD Stub".to_string()),
            size_bytes: 250 * 1024 * 1024 * 1024,
            removable: false,
            is_system_disk: true,
            volumes: vec![
                Volume {
                    id: "/".to_string(),
                    label: Some("Macintosh HD".to_string()),
                    filesystem: Some("APFS".to_string()),
                    size_bytes: 200 * 1024 * 1024 * 1024,
                    mount_points: vec!["/".to_string()],
                }
            ],
        }
    ])
}
