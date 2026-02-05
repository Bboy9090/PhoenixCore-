use anyhow::{anyhow, Result};
use bootforge_core::{DeviceGraph, Disk, HostInfo, Partition};
use std::collections::HashMap;
use std::fs;
use std::path::{Path, PathBuf};

pub fn build_device_graph() -> Result<DeviceGraph> {
    let host = HostInfo {
        os: "linux".to_string(),
        os_version: read_os_release().unwrap_or_else(|| "unknown".to_string()),
        machine: read_machine_name().unwrap_or_else(|| "unknown".to_string()),
    };

    let mounts = read_mounts();
    let labels = read_labels();
    let disks = enumerate_disks(&mounts, &labels)?;
    Ok(DeviceGraph::new(host, disks))
}

fn read_os_release() -> Option<String> {
    let content = fs::read_to_string("/etc/os-release").ok()?;
    for line in content.lines() {
        if let Some(value) = line.strip_prefix("PRETTY_NAME=") {
            return Some(trim_quotes(value));
        }
    }
    None
}

fn read_machine_name() -> Option<String> {
    if let Ok(value) = fs::read_to_string("/etc/hostname") {
        let value = value.trim();
        if !value.is_empty() {
            return Some(value.to_string());
        }
    }
    std::env::var("HOSTNAME").ok()
}

fn enumerate_disks(
    mounts: &HashMap<String, MountInfo>,
    labels: &HashMap<String, String>,
) -> Result<Vec<Disk>> {
    let mut disks = Vec::new();
    let entries = fs::read_dir("/sys/block")?;
    for entry in entries {
        let entry = entry?;
        let name = entry.file_name().to_string_lossy().to_string();
        if should_skip_disk(&name) {
            continue;
        }
        let disk_path = entry.path();
        let size_bytes = read_block_size_bytes(disk_path.join("size"))?;
        let removable = read_bool(disk_path.join("removable")).unwrap_or(false);
        let friendly_name = read_string(disk_path.join("device").join("model"))
            .unwrap_or_else(|| name.clone());

        let mut partitions = Vec::new();
        if let Ok(children) = fs::read_dir(&disk_path) {
            for child in children.flatten() {
                let part_name = child.file_name().to_string_lossy().to_string();
                if !part_name.starts_with(&name) || part_name == name {
                    continue;
                }
                let part_size = read_block_size_bytes(child.path().join("size")).unwrap_or(0);
                let device_path = format!("/dev/{}", part_name);
                let mount_info = mounts.get(&device_path);
                let mount_points = mount_info
                    .map(|info| info.mount_points.clone())
                    .unwrap_or_default();
                let fs_type = mount_info.and_then(|info| info.fs_type.clone());
                let label = labels.get(&device_path).cloned();

                partitions.push(Partition {
                    id: device_path.clone(),
                    label,
                    fs: fs_type,
                    size_bytes: part_size,
                    mount_points,
                });
            }
        }

        let is_system_disk = partitions.iter().any(|partition| {
            partition.mount_points.iter().any(|mount| {
                mount == "/" || mount == "/boot" || mount == "/boot/efi"
            })
        });

        disks.push(Disk {
            id: format!("/dev/{}", name),
            friendly_name,
            size_bytes,
            is_system_disk,
            removable,
            partitions,
        });
    }

    Ok(disks)
}

fn read_mounts() -> HashMap<String, MountInfo> {
    let mut mounts: HashMap<String, MountInfo> = HashMap::new();
    let data = fs::read_to_string("/proc/self/mounts").unwrap_or_default();
    for line in data.lines() {
        let mut parts = line.split_whitespace();
        let device = match parts.next() {
            Some(value) => value,
            None => continue,
        };
        let mount_point = match parts.next() {
            Some(value) => value,
            None => continue,
        };
        let fs_type = match parts.next() {
            Some(value) => value,
            None => continue,
        };
        let entry = mounts.entry(device.to_string()).or_insert_with(|| MountInfo {
            mount_points: Vec::new(),
            fs_type: Some(fs_type.to_string()),
        });
        entry.mount_points.push(mount_point.to_string());
    }
    mounts
}

fn read_labels() -> HashMap<String, String> {
    let mut labels = HashMap::new();
    let root = Path::new("/dev/disk/by-label");
    let entries = match fs::read_dir(root) {
        Ok(entries) => entries,
        Err(_) => return labels,
    };
    for entry in entries.flatten() {
        let label = entry.file_name().to_string_lossy().to_string();
        let target = match fs::read_link(entry.path()) {
            Ok(target) => target,
            Err(_) => continue,
        };
        let resolved = resolve_symlink(root, &target).unwrap_or(target);
        let key = resolved.to_string_lossy().to_string();
        labels.insert(key, label);
    }
    labels
}

fn resolve_symlink(root: &Path, target: &Path) -> Option<PathBuf> {
    let full = if target.is_absolute() {
        target.to_path_buf()
    } else {
        root.join(target)
    };
    full.canonicalize().ok()
}

fn read_block_size_bytes(path: PathBuf) -> Result<u64> {
    let raw = read_string(path).ok_or_else(|| anyhow!("missing size"))?;
    let sectors: u64 = raw.parse().unwrap_or(0);
    Ok(sectors.saturating_mul(512))
}

fn read_string(path: PathBuf) -> Option<String> {
    fs::read_to_string(path).ok().map(|value| value.trim().to_string())
}

fn read_bool(path: PathBuf) -> Option<bool> {
    let value = read_string(path)?;
    Some(value == "1")
}

fn should_skip_disk(name: &str) -> bool {
    name.starts_with("loop")
        || name.starts_with("ram")
        || name.starts_with("sr")
        || name.starts_with("dm-")
        || name.starts_with("zd")
}

fn trim_quotes(value: &str) -> String {
    value.trim_matches('"').to_string()
}

#[derive(Debug, Clone)]
struct MountInfo {
    mount_points: Vec<String>,
    fs_type: Option<String>,
}
