use anyhow::{anyhow, Result};
use phoenix_core::{now_utc_rfc3339, DeviceGraph, HostInfo, Partition};

#[cfg(windows)]
pub mod format;
#[cfg(windows)]
mod volumes;
#[cfg(windows)]
mod win;
#[cfg(not(windows))]
mod format_stub;
#[cfg(not(windows))]
pub use format_stub as format;

pub fn build_device_graph() -> Result<DeviceGraph> {
    #[cfg(windows)]
    {
        let host = HostInfo {
            os: "windows".to_string(),
            os_version: win::os_version_string(),
            machine: win::machine_name_string(),
        };

        let mut disks = win::enumerate_physical_disks()?;
        let sys_drive = volumes::system_drive_letter()?;
        let mounts = volumes::enumerate_volume_mounts()?;

        for disk in disks.iter_mut() {
            let Some(disk_number) = parse_disk_number(&disk.id) else {
                continue;
            };

            let partition_entries = win::enumerate_partitions(disk_number)?;
            let mut partitions = Vec::new();
            for entry in partition_entries {
                let mut label = None;
                let mut fs = None;
                let mut mount_points = Vec::new();
                for mount in mounts.iter().filter(|m| m.disk_number == disk_number) {
                    if mount.offset_bytes >= entry.offset_bytes
                        && mount.offset_bytes < entry.offset_bytes + entry.length_bytes
                    {
                        mount_points.extend(mount.mount_points.clone());
                        if label.is_none() {
                            label = mount.label.clone();
                        }
                        if fs.is_none() {
                            fs = mount.fs.clone();
                        }
                    }
                }

                partitions.push(Partition {
                    id: format!("Disk{}Partition{}", disk_number, entry.number),
                    label,
                    fs,
                    size_bytes: entry.length_bytes,
                    mount_points,
                });
            }

            disk.partitions = partitions;
            disk.is_system_disk = disk.partitions.iter().any(|partition| {
                partition
                    .mount_points
                    .iter()
                    .any(|mount| mount.to_ascii_uppercase().starts_with(&sys_drive))
            });
        }

        let generated_at_utc = now_utc_rfc3339();
        Ok(DeviceGraph::new(host, disks, generated_at_utc))
    }

    #[cfg(not(windows))]
    {
        Err(anyhow!("phoenix-host-windows requires Windows"))
    }
}

fn parse_disk_number(id: &str) -> Option<u32> {
    let suffix = id.strip_prefix("PhysicalDrive")?;
    suffix.parse().ok()
}
