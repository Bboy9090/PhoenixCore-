/// Hardware detection module
/// 
/// Provides comprehensive hardware information detection including GPU, BIOS, and advanced CPU details

use serde::{Deserialize, Serialize};
use std::process::Command;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct GPUInfo {
    pub name: String,
    pub vendor: String,
    pub memory: String,
    pub driver: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BIOSInfo {
    pub vendor: String,
    pub version: String,
    pub release_date: String,
    pub firmware_type: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CPUDetails {
    pub model: String,
    pub cores: usize,
    pub threads: usize,
    pub base_frequency: String,
    pub max_frequency: String,
    pub cache: String,
    pub microcode: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MemoryInfo {
    pub total: String,
    pub available: String,
    pub used: String,
    pub type_: String,
    pub speed: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct StorageInfo {
    pub total: String,
    pub used: String,
    pub available: String,
    pub devices: Vec<String>,
}

/// Detect GPU information
pub fn detect_gpu() -> Result<Vec<GPUInfo>, String> {
    let mut gpus = Vec::new();

    // Try lspci first
    if let Ok(output) = Command::new("lspci")
        .arg("-v")
        .output()
    {
        let stdout = String::from_utf8_lossy(&output.stdout);
        
        // Parse NVIDIA GPUs
        for line in stdout.lines() {
            if line.contains("NVIDIA") && line.contains("VGA") {
                let gpu = parse_nvidia_gpu(line);
                gpus.push(gpu);
            }
            // Parse AMD GPUs
            else if line.contains("AMD") && (line.contains("VGA") || line.contains("Display")) {
                let gpu = parse_amd_gpu(line);
                gpus.push(gpu);
            }
            // Parse Intel GPUs
            else if line.contains("Intel") && line.contains("VGA") {
                let gpu = parse_intel_gpu(line);
                gpus.push(gpu);
            }
        }
    }

    // Try nvidia-smi for NVIDIA GPUs
    if let Ok(output) = Command::new("nvidia-smi")
        .arg("--query-gpu=name,memory.total,driver_version")
        .arg("--format=csv,noheader")
        .output()
    {
        let stdout = String::from_utf8_lossy(&output.stdout);
        for line in stdout.lines() {
            let parts: Vec<&str> = line.split(',').collect();
            if parts.len() >= 3 {
                gpus.push(GPUInfo {
                    name: parts[0].trim().to_string(),
                    vendor: "NVIDIA".to_string(),
                    memory: parts[1].trim().to_string(),
                    driver: parts[2].trim().to_string(),
                });
            }
        }
    }

    // Try glxinfo for OpenGL info
    if let Ok(output) = Command::new("glxinfo")
        .arg("-B")
        .output()
    {
        let stdout = String::from_utf8_lossy(&output.stdout);
        for line in stdout.lines() {
            if line.contains("OpenGL renderer") {
                let gpu_name = line.split(':').nth(1).unwrap_or("Unknown").trim().to_string();
                if !gpus.iter().any(|g| g.name == gpu_name) {
                    gpus.push(GPUInfo {
                        name: gpu_name,
                        vendor: "Unknown".to_string(),
                        memory: "Unknown".to_string(),
                        driver: "Unknown".to_string(),
                    });
                }
            }
        }
    }

    if gpus.is_empty() {
        gpus.push(GPUInfo {
            name: "Integrated Graphics".to_string(),
            vendor: "Unknown".to_string(),
            memory: "Shared System Memory".to_string(),
            driver: "Unknown".to_string(),
        });
    }

    Ok(gpus)
}

/// Detect BIOS information
pub fn detect_bios() -> Result<BIOSInfo, String> {
    // Try dmidecode first (requires root)
    if let Ok(output) = Command::new("sudo")
        .arg("dmidecode")
        .arg("-t")
        .arg("0")
        .output()
    {
        if output.status.success() {
            return Ok(parse_dmidecode_bios(&String::from_utf8_lossy(&output.stdout)));
        }
    }

    // Fallback: read from /sys/class/dmi/id/
    let vendor = read_dmi_file("sys_vendor").unwrap_or_else(|_| "Unknown".to_string());
    let version = read_dmi_file("bios_version").unwrap_or_else(|_| "Unknown".to_string());
    let release_date = read_dmi_file("bios_date").unwrap_or_else(|_| "Unknown".to_string());

    Ok(BIOSInfo {
        vendor,
        version,
        release_date,
        firmware_type: detect_firmware_type(),
    })
}

/// Detect CPU details
pub fn detect_cpu_details() -> Result<CPUDetails, String> {
    // Read from /proc/cpuinfo
    let cpuinfo = std::fs::read_to_string("/proc/cpuinfo")
        .map_err(|e| format!("Failed to read /proc/cpuinfo: {}", e))?;

    let mut model = String::new();
    let mut cores = 0;
    let mut threads = 0;
    let mut base_freq = String::new();
    let mut max_freq = String::new();
    let mut cache = String::new();
    let mut microcode = String::new();

    for line in cpuinfo.lines() {
        if line.starts_with("model name") {
            model = line.split(':').nth(1).unwrap_or("Unknown").trim().to_string();
        } else if line.starts_with("cpu cores") {
            cores = line.split(':').nth(1).unwrap_or("0").trim().parse().unwrap_or(0);
        } else if line.starts_with("siblings") {
            threads = line.split(':').nth(1).unwrap_or("0").trim().parse().unwrap_or(0);
        } else if line.starts_with("cpu MHz") {
            base_freq = format!("{} MHz", line.split(':').nth(1).unwrap_or("0").trim());
        } else if line.starts_with("cache size") {
            cache = line.split(':').nth(1).unwrap_or("Unknown").trim().to_string();
        } else if line.starts_with("microcode") {
            microcode = line.split(':').nth(1).unwrap_or("Unknown").trim().to_string();
        }
    }

    // Try to get max frequency from cpufreq
    if let Ok(max_freq_str) = std::fs::read_to_string("/sys/devices/system/cpu/cpu0/cpufreq/cpuinfo_max_freq") {
        if let Ok(freq_khz) = max_freq_str.trim().parse::<u64>() {
            max_freq = format!("{} MHz", freq_khz / 1000);
        }
    }

    Ok(CPUDetails {
        model,
        cores,
        threads,
        base_frequency: base_freq,
        max_frequency: max_freq,
        cache,
        microcode,
    })
}

/// Detect memory information
pub fn detect_memory_info() -> Result<MemoryInfo, String> {
    let meminfo = std::fs::read_to_string("/proc/meminfo")
        .map_err(|e| format!("Failed to read /proc/meminfo: {}", e))?;

    let mut total = String::new();
    let mut available = String::new();
    let mut used = String::new();

    for line in meminfo.lines() {
        if line.starts_with("MemTotal") {
            total = format_memory(line.split(':').nth(1).unwrap_or("0").trim());
        } else if line.starts_with("MemAvailable") {
            available = format_memory(line.split(':').nth(1).unwrap_or("0").trim());
        } else if line.starts_with("MemFree") {
            used = format_memory(line.split(':').nth(1).unwrap_or("0").trim());
        }
    }

    // Try to detect memory type and speed
    let (mem_type, speed) = detect_memory_type_and_speed();

    Ok(MemoryInfo {
        total,
        available,
        used,
        type_: mem_type,
        speed,
    })
}

/// Detect storage information
pub fn detect_storage_info() -> Result<StorageInfo, String> {
    let mut total = String::new();
    let mut used = String::new();
    let mut available = String::new();
    let mut devices = Vec::new();

    // Use df to get storage info
    if let Ok(output) = Command::new("df")
        .arg("-h")
        .arg("/")
        .output()
    {
        let stdout = String::from_utf8_lossy(&output.stdout);
        for line in stdout.lines().skip(1) {
            let parts: Vec<&str> = line.split_whitespace().collect();
            if parts.len() >= 4 {
                total = parts[1].to_string();
                used = parts[2].to_string();
                available = parts[3].to_string();
                devices.push(parts[0].to_string());
            }
        }
    }

    // Get all block devices
    if let Ok(output) = Command::new("lsblk")
        .arg("-d")
        .arg("-n")
        .arg("-o")
        .arg("NAME")
        .output()
    {
        let stdout = String::from_utf8_lossy(&output.stdout);
        for line in stdout.lines() {
            devices.push(format!("/dev/{}", line.trim()));
        }
    }

    Ok(StorageInfo {
        total,
        used,
        available,
        devices,
    })
}

// Helper functions

fn parse_nvidia_gpu(line: &str) -> GPUInfo {
    GPUInfo {
        name: line.to_string(),
        vendor: "NVIDIA".to_string(),
        memory: "Unknown".to_string(),
        driver: "Unknown".to_string(),
    }
}

fn parse_amd_gpu(line: &str) -> GPUInfo {
    GPUInfo {
        name: line.to_string(),
        vendor: "AMD".to_string(),
        memory: "Unknown".to_string(),
        driver: "Unknown".to_string(),
    }
}

fn parse_intel_gpu(line: &str) -> GPUInfo {
    GPUInfo {
        name: line.to_string(),
        vendor: "Intel".to_string(),
        memory: "Shared".to_string(),
        driver: "Unknown".to_string(),
    }
}

fn parse_dmidecode_bios(output: &str) -> BIOSInfo {
    let mut vendor = String::new();
    let mut version = String::new();
    let mut release_date = String::new();

    for line in output.lines() {
        if line.contains("Vendor") {
            vendor = line.split(':').nth(1).unwrap_or("Unknown").trim().to_string();
        } else if line.contains("Version") {
            version = line.split(':').nth(1).unwrap_or("Unknown").trim().to_string();
        } else if line.contains("Release Date") {
            release_date = line.split(':').nth(1).unwrap_or("Unknown").trim().to_string();
        }
    }

    BIOSInfo {
        vendor,
        version,
        release_date,
        firmware_type: detect_firmware_type(),
    }
}

fn read_dmi_file(filename: &str) -> Result<String, String> {
    std::fs::read_to_string(format!("/sys/class/dmi/id/{}", filename))
        .map(|s| s.trim().to_string())
        .map_err(|e| format!("Failed to read DMI file: {}", e))
}

fn detect_firmware_type() -> String {
    if std::path::Path::new("/sys/firmware/efi").exists() {
        "UEFI".to_string()
    } else {
        "BIOS".to_string()
    }
}

fn format_memory(kb_str: &str) -> String {
    if let Ok(kb) = kb_str.parse::<u64>() {
        let gb = kb / 1024 / 1024;
        let mb = (kb / 1024) % 1024;
        format!("{} GB {} MB", gb, mb)
    } else {
        "Unknown".to_string()
    }
}

fn detect_memory_type_and_speed() -> (String, String) {
    let mut mem_type = "Unknown".to_string();
    let mut speed = "Unknown".to_string();

    // Try dmidecode
    if let Ok(output) = Command::new("sudo")
        .arg("dmidecode")
        .arg("-t")
        .arg("17")
        .output()
    {
        let stdout = String::from_utf8_lossy(&output.stdout);
        for line in stdout.lines() {
            if line.contains("Type:") {
                mem_type = line.split(':').nth(1).unwrap_or("Unknown").trim().to_string();
            } else if line.contains("Speed:") {
                speed = line.split(':').nth(1).unwrap_or("Unknown").trim().to_string();
            }
        }
    }

    (mem_type, speed)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_format_memory() {
        assert_eq!(format_memory("1048576"), "1 GB 0 MB");
        assert_eq!(format_memory("2097152"), "2 GB 0 MB");
    }

    #[test]
    fn test_firmware_type_detection() {
        let firmware = detect_firmware_type();
        assert!(firmware == "UEFI" || firmware == "BIOS");
    }
}
