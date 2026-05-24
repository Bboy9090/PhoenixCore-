// Phoenix OS — Phoenix Control Center: System Commands
// File: apps/phoenix-control-center/src/commands.rs
//
// Tauri command handlers for system information queries.
// All commands are read-only — no system state is modified here.

use serde::{Deserialize, Serialize};
use std::process::Command;

#[derive(Debug, Serialize, Deserialize)]
pub struct SystemInfo {
    pub hostname:       String,
    pub os_name:        String,
    pub os_version:     String,
    pub kernel_version: String,
    pub uptime_seconds: u64,
    pub cpu_count:      usize,
    pub total_ram_bytes: u64,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct CpuInfo {
    pub model_name:     String,
    pub core_count:     usize,
    pub thread_count:   usize,
    pub frequency_mhz:  f64,
    pub usage_percent:  f32,
    pub temperature_celsius: Option<f32>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct MemoryInfo {
    pub total_bytes:     u64,
    pub available_bytes: u64,
    pub used_bytes:      u64,
    pub used_percent:    f32,
    pub swap_total_bytes: u64,
    pub swap_used_bytes:  u64,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct ThermalSensor {
    pub name:               String,
    pub temperature_celsius: f32,
    pub high_threshold:     Option<f32>,
    pub critical_threshold: Option<f32>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct ThermalInfo {
    pub sensors: Vec<ThermalSensor>,
}

/// Get high-level system information.
#[tauri::command]
pub fn get_system_info() -> Result<SystemInfo, String> {
    let hostname = read_file_trimmed("/etc/hostname")
        .unwrap_or_else(|| "unknown".to_string());

    let os_name = read_os_release("PRETTY_NAME")
        .unwrap_or_else(|| "Phoenix OS".to_string());

    let os_version = read_os_release("VERSION_ID")
        .unwrap_or_else(|| "unknown".to_string());

    let kernel_version = run_command("uname", &["-r"])
        .unwrap_or_else(|| "unknown".to_string());

    let uptime_seconds = read_file_trimmed("/proc/uptime")
        .and_then(|s| s.split_whitespace().next().map(String::from))
        .and_then(|s| s.parse::<f64>().ok())
        .map(|f| f as u64)
        .unwrap_or(0);

    let cpu_count = read_file("/proc/cpuinfo")
        .map(|s| s.lines().filter(|l| l.starts_with("processor")).count())
        .unwrap_or(1);

    let total_ram_bytes = read_meminfo("MemTotal")
        .map(|kb| kb * 1024)
        .unwrap_or(0);

    Ok(SystemInfo {
        hostname,
        os_name,
        os_version,
        kernel_version,
        uptime_seconds,
        cpu_count,
        total_ram_bytes,
    })
}

/// Get CPU model, frequency, and usage.
#[tauri::command]
pub fn get_cpu_info() -> Result<CpuInfo, String> {
    let cpuinfo = read_file("/proc/cpuinfo").unwrap_or_default();

    let model_name = cpuinfo
        .lines()
        .find(|l| l.starts_with("model name"))
        .and_then(|l| l.split(':').nth(1))
        .map(|s| s.trim().to_string())
        .unwrap_or_else(|| "Unknown CPU".to_string());

    let thread_count = cpuinfo
        .lines()
        .filter(|l| l.starts_with("processor"))
        .count();

    let core_count = cpuinfo
        .lines()
        .find(|l| l.starts_with("cpu cores"))
        .and_then(|l| l.split(':').nth(1))
        .and_then(|s| s.trim().parse().ok())
        .unwrap_or(thread_count);

    // Read current frequency from cpufreq (in kHz)
    let freq_khz: f64 = std::fs::read_to_string(
        "/sys/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq"
    )
    .ok()
    .and_then(|s| s.trim().parse().ok())
    .unwrap_or(0.0);

    let frequency_mhz = freq_khz / 1000.0;

    // CPU usage: read /proc/stat twice with a small delay
    let usage_percent = read_cpu_usage();

    // Temperature from hwmon / thermal zones
    let temperature_celsius = read_cpu_temperature();

    Ok(CpuInfo {
        model_name,
        core_count,
        thread_count,
        frequency_mhz,
        usage_percent,
        temperature_celsius,
    })
}

/// Get memory (RAM + swap) statistics.
#[tauri::command]
pub fn get_memory_info() -> Result<MemoryInfo, String> {
    let total_bytes     = read_meminfo("MemTotal").map(|kb| kb * 1024).unwrap_or(0);
    let available_bytes = read_meminfo("MemAvailable").map(|kb| kb * 1024).unwrap_or(0);
    let used_bytes      = total_bytes.saturating_sub(available_bytes);
    let used_percent    = if total_bytes > 0 {
        (used_bytes as f32 / total_bytes as f32) * 100.0
    } else {
        0.0
    };
    let swap_total_bytes = read_meminfo("SwapTotal").map(|kb| kb * 1024).unwrap_or(0);
    let swap_free_bytes  = read_meminfo("SwapFree").map(|kb| kb * 1024).unwrap_or(0);
    let swap_used_bytes  = swap_total_bytes.saturating_sub(swap_free_bytes);

    Ok(MemoryInfo {
        total_bytes,
        available_bytes,
        used_bytes,
        used_percent,
        swap_total_bytes,
        swap_used_bytes,
    })
}

/// Get hardware thermal sensor readings.
#[tauri::command]
pub fn get_thermal_info() -> Result<ThermalInfo, String> {
    let mut sensors = Vec::new();

    // Read from /sys/class/thermal/thermal_zone*/
    if let Ok(entries) = std::fs::read_dir("/sys/class/thermal") {
        for entry in entries.flatten() {
            let path = entry.path();
            let name = path.file_name()
                .and_then(|n| n.to_str())
                .unwrap_or("")
                .to_string();

            if !name.starts_with("thermal_zone") {
                continue;
            }

            let temp_raw = std::fs::read_to_string(path.join("temp"))
                .ok()
                .and_then(|s| s.trim().parse::<i64>().ok());

            let zone_type = std::fs::read_to_string(path.join("type"))
                .map(|s| s.trim().to_string())
                .unwrap_or_else(|_| name.clone());

            if let Some(temp_millidegrees) = temp_raw {
                sensors.push(ThermalSensor {
                    name: zone_type,
                    temperature_celsius: temp_millidegrees as f32 / 1000.0,
                    high_threshold: None,
                    critical_threshold: None,
                });
            }
        }
    }

    Ok(ThermalInfo { sensors })
}

// ---- Private helpers ----

fn read_file(path: &str) -> Option<String> {
    std::fs::read_to_string(path).ok()
}

fn read_file_trimmed(path: &str) -> Option<String> {
    read_file(path).map(|s| s.trim().to_string())
}

fn read_os_release(key: &str) -> Option<String> {
    let content = read_file("/etc/os-release")?;
    for line in content.lines() {
        if let Some(val) = line.strip_prefix(&format!("{}=", key)) {
            return Some(val.trim_matches('"').to_string());
        }
    }
    None
}

fn read_meminfo(key: &str) -> Option<u64> {
    let content = read_file("/proc/meminfo")?;
    for line in content.lines() {
        if line.starts_with(key) {
            return line.split_whitespace().nth(1)?.parse().ok();
        }
    }
    None
}

fn run_command(cmd: &str, args: &[&str]) -> Option<String> {
    Command::new(cmd)
        .args(args)
        .output()
        .ok()
        .map(|o| String::from_utf8_lossy(&o.stdout).trim().to_string())
}

fn read_cpu_usage() -> f32 {
    // Read /proc/stat twice with 100ms gap to compute usage delta
    let read_stat = || -> Option<(u64, u64)> {
        let content = read_file("/proc/stat")?;
        let line = content.lines().next()?; // "cpu  user nice system idle ..."
        let parts: Vec<u64> = line
            .split_whitespace()
            .skip(1)
            .filter_map(|s| s.parse().ok())
            .collect();
        if parts.len() < 4 { return None; }
        let idle  = parts[3];
        let total: u64 = parts.iter().sum();
        Some((idle, total))
    };

    let first = read_stat();
    std::thread::sleep(std::time::Duration::from_millis(100));
    let second = read_stat();

    match (first, second) {
        (Some((idle1, total1)), Some((idle2, total2))) => {
            let d_total = total2.saturating_sub(total1) as f32;
            let d_idle  = idle2.saturating_sub(idle1) as f32;
            if d_total > 0.0 {
                (1.0 - d_idle / d_total) * 100.0
            } else {
                0.0
            }
        }
        _ => 0.0,
    }
}

fn read_cpu_temperature() -> Option<f32> {
    // Try thermal_zone0 first (usually CPU on x86)
    let temp_raw = std::fs::read_to_string("/sys/class/thermal/thermal_zone0/temp")
        .ok()
        .and_then(|s| s.trim().parse::<i64>().ok())?;
    Some(temp_raw as f32 / 1000.0)
}
