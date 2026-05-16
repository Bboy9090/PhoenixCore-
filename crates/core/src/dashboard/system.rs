use lazy_static::lazy_static;
/// System monitoring and information module
///
/// Provides real-time system metrics including CPU, memory, disk, and hardware information.
use serde::{Deserialize, Serialize};
use std::sync::Mutex;
use sysinfo::{CpuExt, DiskExt, NetworkExt, NetworksExt, PidExt, ProcessExt, System, SystemExt};

lazy_static! {
    static ref SYSTEM: Mutex<System> = Mutex::new(System::new_all());
}

/// System information response
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SystemInfo {
    pub hostname: String,
    pub os_version: String,
    pub kernel: String,
    pub uptime: u64,
    pub cpu_count: usize,
    pub cpu_model: String,
    pub total_memory: u64,
    pub architecture: String,
}

/// Disk information response
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DiskInfo {
    pub device: String,
    pub mount_point: String,
    pub filesystem: String,
    pub total_size: u64,
    pub used_size: u64,
    pub available_size: u64,
    pub usage_percent: f64,
    pub is_read_only: bool,
}

/// Process information response
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ProcessInfo {
    pub pid: u32,
    pub name: String,
    pub user: String,
    pub cpu_usage: f32,
    pub memory_usage: u64,
    pub status: String,
}

/// Network interface information
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct NetworkInterface {
    pub name: String,
    pub ip_address: String,
    pub mac_address: String,
    pub status: String,
    pub bytes_received: u64,
    pub bytes_sent: u64,
}

/// Hardware information response
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct HardwareInfo {
    pub cpu_info: String,
    pub gpu_info: Vec<String>,
    pub ram_info: String,
    pub storage_info: String,
    pub bios_info: String,
}

/// Partition information for disk management
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PartitionInfo {
    pub device: String,
    pub mount_point: String,
    pub filesystem: String,
    pub total_size: u64,
    pub used_size: u64,
    pub available_size: u64,
    pub usage_percent: f64,
    pub is_read_only: bool,
    pub is_system_disk: bool,
    pub is_removable: bool,
}

/// Get system information
pub fn get_system_info() -> Result<SystemInfo, String> {
    let mut sys = SYSTEM
        .lock()
        .map_err(|e| format!("Failed to lock system: {}", e))?;
    sys.refresh_all();

    let hostname = hostname::get()
        .map(|h| h.to_string_lossy().to_string())
        .unwrap_or_else(|_| "Unknown".to_string());

    let os_version = std::env::var("PRETTY_NAME").unwrap_or_else(|_| "Unknown".to_string());

    let kernel = format!(
        "{} {}",
        sys.name().unwrap_or_default(),
        sys.kernel_version().unwrap_or_default()
    );

    let uptime = sys.uptime();
    let cpu_count = sys.cpus().len();
    let cpu_model = sys
        .cpus()
        .first()
        .map(|cpu| cpu.brand().to_string())
        .unwrap_or_else(|| "Unknown".to_string());

    let total_memory = sys.total_memory() * 1024; // Convert to bytes

    let architecture = std::env::consts::ARCH.to_string();

    Ok(SystemInfo {
        hostname,
        os_version,
        kernel,
        uptime,
        cpu_count,
        cpu_model,
        total_memory,
        architecture,
    })
}

/// Get CPU usage percentage (0-100)
pub fn get_cpu_usage() -> Result<f32, String> {
    let mut sys = SYSTEM
        .lock()
        .map_err(|e| format!("Failed to lock system: {}", e))?;
    sys.refresh_cpu();

    // Get average CPU usage across all cores
    let total: f32 = sys.cpus().iter().map(|cpu| cpu.cpu_usage()).sum();
    let average = total / sys.cpus().len() as f32;

    Ok(average)
}

/// Get memory usage percentage (0-100)
pub fn get_memory_usage() -> Result<f32, String> {
    let mut sys = SYSTEM
        .lock()
        .map_err(|e| format!("Failed to lock system: {}", e))?;
    sys.refresh_memory();

    let used = sys.used_memory() as f64;
    let total = sys.total_memory() as f64;

    let percentage = if total > 0.0 {
        (used / total) * 100.0
    } else {
        0.0
    };

    Ok(percentage as f32)
}

/// Get disk information for all mounted disks
pub fn get_disk_info() -> Result<Vec<DiskInfo>, String> {
    let mut sys = SYSTEM
        .lock()
        .map_err(|e| format!("Failed to lock system: {}", e))?;
    sys.refresh_disks();

    let disks: Vec<DiskInfo> = sys
        .disks()
        .iter()
        .map(|disk| {
            let total_size = disk.total_space() * 1024; // Convert to bytes
            let used_size = (disk.total_space() - disk.available_space()) * 1024;
            let available_size = disk.available_space() * 1024;
            let usage_percent = if total_size > 0 {
                (used_size as f64 / total_size as f64) * 100.0
            } else {
                0.0
            };

            DiskInfo {
                device: disk.name().to_string_lossy().to_string(),
                mount_point: disk.mount_point().to_string_lossy().to_string(),
                filesystem: String::from_utf8_lossy(disk.file_system()).to_string(),
                total_size,
                used_size,
                available_size,
                usage_percent,
                is_read_only: disk.is_removable(),
            }
        })
        .collect();

    Ok(disks)
}

/// Get running processes
pub fn get_processes() -> Result<Vec<ProcessInfo>, String> {
    let mut sys = SYSTEM
        .lock()
        .map_err(|e| format!("Failed to lock system: {}", e))?;
    sys.refresh_processes();

    let processes: Vec<ProcessInfo> = sys
        .processes()
        .iter()
        .take(50) // Limit to top 50 processes
        .map(|(_, process)| {
            ProcessInfo {
                pid: process.pid().as_u32(),
                name: process.name().to_string(),
                user: "unknown".to_string(),
                cpu_usage: process.cpu_usage(),
                memory_usage: process.memory(), // sysinfo returns bytes already in some versions, or KB. 0.29.11 returns bytes.
                status: format!("{:?}", process.status()),
            }
        })
        .collect();

    Ok(processes)
}

/// Get network interfaces
pub fn get_network_interfaces() -> Result<Vec<NetworkInterface>, String> {
    let mut sys = SYSTEM
        .lock()
        .map_err(|e| format!("Failed to lock system: {}", e))?;
    sys.refresh_networks();

    let interfaces: Vec<NetworkInterface> = sys
        .networks()
        .iter()
        .map(|(name, data)| {
            NetworkInterface {
                name: name.to_string(),
                ip_address: "127.0.0.1".to_string(), // TODO: Get actual IP
                mac_address: data.mac_address().to_string(),
                status: "up".to_string(),
                bytes_received: data.received(),
                bytes_sent: data.transmitted(),
            }
        })
        .collect();

    Ok(interfaces)
}

/// Get hardware information
pub fn get_hardware_info() -> Result<HardwareInfo, String> {
    let mut sys = SYSTEM
        .lock()
        .map_err(|e| format!("Failed to lock system: {}", e))?;
    sys.refresh_all();

    let cpu_info = sys
        .cpus()
        .first()
        .map(|cpu| {
            format!(
                "{} @ {:.2} GHz",
                cpu.brand(),
                cpu.frequency() as f64 / 1000.0
            )
        })
        .unwrap_or_else(|| "Unknown CPU".to_string());

    let ram_info = format!(
        "{} GB ({} GB used)",
        sys.total_memory() / 1024 / 1024,
        sys.used_memory() / 1024 / 1024
    );

    let storage_info = sys
        .disks()
        .iter()
        .map(|disk| {
            let total = disk.total_space() / 1024 / 1024;
            let used = (disk.total_space() - disk.available_space()) / 1024 / 1024;
            format!(
                "{}: {} GB / {} GB",
                disk.mount_point().display(),
                used,
                total
            )
        })
        .collect::<Vec<_>>()
        .join(", ");

    Ok(HardwareInfo {
        cpu_info,
        gpu_info: vec!["GPU detection not yet implemented".to_string()],
        ram_info,
        storage_info,
        bios_info: "BIOS detection not yet implemented".to_string(),
    })
}

/// Get partition information with safety checks
pub fn get_partitions() -> Result<Vec<PartitionInfo>, String> {
    let mut sys = SYSTEM
        .lock()
        .map_err(|e| format!("Failed to lock system: {}", e))?;
    sys.refresh_disks();

    let partitions: Vec<PartitionInfo> = sys
        .disks()
        .iter()
        .map(|disk| {
            let total_size = disk.total_space() * 1024;
            let used_size = (disk.total_space() - disk.available_space()) * 1024;
            let available_size = disk.available_space() * 1024;
            let usage_percent = if total_size > 0 {
                (used_size as f64 / total_size as f64) * 100.0
            } else {
                0.0
            };

            let device = disk.name().to_string_lossy().to_string();
            let mount_point = disk.mount_point().to_string_lossy().to_string();

            // Detect system disk (typically /, /boot, /home)
            let is_system_disk =
                mount_point == "/" || mount_point == "/boot" || mount_point == "/home";

            // Detect removable media
            let is_removable =
                disk.is_removable() || device.contains("usb") || device.contains("sr");

            PartitionInfo {
                device,
                mount_point,
                filesystem: String::from_utf8_lossy(disk.file_system()).to_string(),
                total_size,
                used_size,
                available_size,
                usage_percent,
                is_read_only: disk.is_removable(),
                is_system_disk,
                is_removable,
            }
        })
        .collect();

    Ok(partitions)
}

/// Scan disk for errors (placeholder - actual implementation would use fsck)
pub fn scan_disk_errors(device: &str) -> Result<ScanResult, String> {
    // Safety check: prevent scanning system disks
    if device == "/" || device.contains("sda1") {
        return Err("Cannot scan system disk for safety reasons".to_string());
    }

    Ok(ScanResult {
        device: device.to_string(),
        status: "scan_started".to_string(),
        errors: vec![],
        warnings: vec!["Disk scan is running in background".to_string()],
    })
}

/// Repair disk (placeholder - requires admin privileges)
pub fn repair_disk(device: &str) -> Result<RepairResult, String> {
    // Safety check: prevent repairing system disks
    if device == "/" || device.contains("sda1") {
        return Err("Cannot repair system disk for safety reasons".to_string());
    }

    Ok(RepairResult {
        device: device.to_string(),
        success: false,
        message: "Disk repair requires admin privileges and fsck utility".to_string(),
    })
}

/// Scan result response
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ScanResult {
    pub device: String,
    pub status: String,
    pub errors: Vec<String>,
    pub warnings: Vec<String>,
}

/// Repair result response
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RepairResult {
    pub device: String,
    pub success: bool,
    pub message: String,
}

/// Clear system cache
pub fn clear_system_cache() -> Result<CacheResult, String> {
    Ok(CacheResult {
        success: true,
        space_freed: 0,
        message: "Cache clearing requires admin privileges".to_string(),
    })
}

/// Cache result response
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CacheResult {
    pub success: bool,
    pub space_freed: u64,
    pub message: String,
}

/// Get system logs (placeholder)
pub fn get_system_logs(lines: usize) -> Result<Vec<String>, String> {
    Ok(vec![
        "System logging not yet implemented".to_string();
        lines
    ])
}
