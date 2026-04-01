use anyhow::{Context, Result};
use phoenix_core::{now_utc_rfc3339, DeviceGraph, Disk, HostInfo, Partition};
use std::collections::HashMap;
use std::fs;
use std::path::{Path, PathBuf};

pub fn build_device_graph() -> Result<DeviceGraph> {
    let host = HostInfo {
        os: "linux".to_string(),
        os_version: read_os_release(),
        machine: read_machine(),
    };
    let disks = enumerate_disks()?;
    Ok(DeviceGraph::new(host, disks, now_utc_rfc3339()))
}

fn enumerate_disks() -> Result<Vec<Disk>> {
    let mounts = read_mounts();
    let labels = read_labels();
    let mut disks = Vec::new();
    let entries = fs::read_dir("/sys/block").context("read /sys/block")?;
    for entry in entries {
        let entry = entry?;
        let disk_name = entry.file_name().to_string_lossy().to_string();
        if is_virtual_disk(&disk_name, entry.path()) {
            continue;
        }
        let size_bytes = read_u64(entry.path().join("size"))
            .map(|sectors| sectors.saturating_mul(512))
            .unwrap_or(0);
        let removable = read_u64(entry.path().join("removable")).unwrap_or(0) == 1;
        let model = read_string(entry.path().join("device/model"))
            .unwrap_or_else(|| disk_name.clone());
        let partitions = enumerate_partitions(&disk_name, entry.path(), &mounts, &labels)?;
        let is_system_disk = partitions.iter().any(|partition| {
            partition.mount_points.iter().any(|mount| mount == "/")
        });
        disks.push(Disk {
            id: disk_name,
            friendly_name: model,
            size_bytes,
            removable,
            is_system_disk,
            partitions,
        });
    }
    Ok(disks)
}

fn enumerate_partitions(
    disk: &str,
    disk_path: PathBuf,
    mounts: &HashMap<String, Vec<MountInfo>>,
    labels: &HashMap<String, String>,
) -> Result<Vec<Partition>> {
    let mut partitions = Vec::new();
    let entries = fs::read_dir(&disk_path).context("read disk entries")?;
    for entry in entries {
        let entry = entry?;
        let path = entry.path();
        if !path.join("partition").exists() {
            continue;
        }
        let part_name = entry.file_name().to_string_lossy().to_string();
        let size_bytes = read_u64(path.join("size"))
            .map(|sectors| sectors.saturating_mul(512))
            .unwrap_or(0);
        let mount_infos = mounts.get(&part_name).cloned().unwrap_or_default();
        let mount_points = mount_infos.iter().map(|info| info.mount_point.clone()).collect();
        let fs_type = mount_infos.first().map(|info| info.fs_type.clone());
        let label = labels.get(&part_name).cloned();
        partitions.push(Partition {
            id: part_name,
            label,
            fs: fs_type,
            size_bytes,
            mount_points,
        });
    }
    Ok(partitions)
}

#[derive(Debug, Clone)]
struct MountInfo {
    mount_point: String,
    fs_type: String,
}

fn read_mounts() -> HashMap<String, Vec<MountInfo>> {
    let mut mounts: HashMap<String, Vec<MountInfo>> = HashMap::new();
    let data = fs::read_to_string("/proc/self/mounts").unwrap_or_default();
    for line in data.lines() {
        let mut parts = line.split_whitespace();
        let device = match parts.next() {
            Some(value) => value,
            None => continue,
        };
        let mount_point = match parts.next() {
            Some(value) => unescape_mount(value),
            None => continue,
        };
        let fs_type = match parts.next() {
            Some(value) => value.to_string(),
            None => continue,
        };
        if !device.starts_with("/dev/") {
            continue;
        }
        let name = Path::new(device)
            .file_name()
            .and_then(|value| value.to_str())
            .unwrap_or("")
            .to_string();
        if name.is_empty() {
            continue;
        }
        mounts.entry(name).or_default().push(MountInfo { mount_point, fs_type });
    }
    mounts
}

fn read_labels() -> HashMap<String, String> {
    let mut labels = HashMap::new();
    let path = Path::new("/dev/disk/by-label");
    if let Ok(entries) = fs::read_dir(path) {
        for entry in entries.flatten() {
            if let Ok(target) = fs::read_link(entry.path()) {
                if let Some(name) = target.file_name().and_then(|v| v.to_str()) {
                    labels.insert(name.to_string(), entry.file_name().to_string_lossy().to_string());
                }
            }
        }
    }
    labels
}

fn read_os_release() -> String {
    let data = fs::read_to_string("/etc/os-release").unwrap_or_default();
    let mut name = None;
    let mut version = None;
    for line in data.lines() {
        if line.starts_with("NAME=") && name.is_none() {
            name = Some(trim_os_value(line));
        } else if line.starts_with("VERSION=") && version.is_none() {
            version = Some(trim_os_value(line));
        }
    }
    match (name, version) {
        (Some(name), Some(version)) => format!("{} {}", name, version),
        (Some(name), None) => name,
        _ => "unknown".to_string(),
    }
}

fn trim_os_value(line: &str) -> String {
    let value = line.splitn(2, '=').nth(1).unwrap_or("").trim();
    value.trim_matches('"').to_string()
}

fn read_machine() -> String {
    let vendor = read_string("/sys/devices/virtual/dmi/id/sys_vendor");
    let product = read_string("/sys/devices/virtual/dmi/id/product_name");
    match (vendor, product) {
        (Some(vendor), Some(product)) => format!("{} {}", vendor, product),
        (Some(vendor), None) => vendor,
        (None, Some(product)) => product,
        _ => read_string("/proc/sys/kernel/hostname").unwrap_or_else(|| "unknown".to_string()),
    }
}

fn read_string(path: impl AsRef<Path>) -> Option<String> {
    fs::read_to_string(path).ok().map(|value| value.trim().to_string())
}

fn read_u64(path: impl AsRef<Path>) -> Option<u64> {
    read_string(path).and_then(|value| value.parse::<u64>().ok())
}

fn unescape_mount(value: &str) -> String {
    let mut output = String::new();
    let mut chars = value.chars().peekable();
    while let Some(ch) = chars.next() {
        if ch == '\\' {
            let mut octal = String::new();
            for _ in 0..3 {
                if let Some(next) = chars.peek() {
                    if next.is_ascii_digit() {
                        octal.push(*next);
                        chars.next();
                    } else {
                        break;
                    }
                }
            }
            if octal.len() == 3 {
                if let Ok(byte) = u8::from_str_radix(&octal, 8) {
                    output.push(byte as char);
                    continue;
                }
            }
            output.push('\\');
            output.push_str(&octal);
        } else {
            output.push(ch);
        }
    }
    output
}

fn is_virtual_disk(name: &str, path: PathBuf) -> bool {
    if name.starts_with("loop") || name.starts_with("ram") || name.starts_with("zram") {
        return true;
    }
    if let Ok(target) = fs::canonicalize(path.join("device")) {
        if target.to_string_lossy().contains("/virtual/") {
            return true;
        }
    }
    false
}
