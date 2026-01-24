use anyhow::{anyhow, Result};
use phoenix_core::{now_utc_rfc3339, DeviceGraph, HostInfo};

#[cfg(windows)]
mod volumes;
#[cfg(windows)]
mod win;

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
        let vol_map = volumes::map_volumes_to_disks()?;

        for disk in disks.iter_mut() {
            if let Some(volumes) = vol_map.get(&disk.id) {
                disk.volumes = volumes.clone();
            }
            disk.is_system_disk = disk.volumes.iter().any(|volume| {
                volume
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
