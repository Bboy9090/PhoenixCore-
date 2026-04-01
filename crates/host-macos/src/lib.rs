use anyhow::{anyhow, Result};
use phoenix_core::{now_utc_rfc3339, DeviceGraph, Disk, HostInfo, Partition};

pub fn build_device_graph() -> Result<DeviceGraph> {
    #[cfg(target_os = "macos")]
    {
        let host = HostInfo {
            os: "macos".to_string(),
            os_version: read_os_version(),
            machine: read_machine(),
        };
        let disks = enumerate_disks()?;
        Ok(DeviceGraph::new(host, disks, now_utc_rfc3339()))
    }

    #[cfg(not(target_os = "macos"))]
    {
        Err(anyhow!("phoenix-host-macos requires macOS"))
    }
}

#[cfg(target_os = "macos")]
fn enumerate_disks() -> Result<Vec<Disk>> {
    let mounts = read_mounts()?;
    let mut disks = std::collections::HashMap::new();
    for mount in mounts {
        if !mount.device.starts_with("/dev/") {
            continue;
        }
        let device_name = mount
            .device
            .split('/')
            .last()
            .unwrap_or("")
            .to_string();
        if device_name.is_empty() {
            continue;
        }
        let disk_id = split_disk_id(&device_name);
        let entry = disks.entry(disk_id.clone()).or_insert_with(|| Disk {
            id: disk_id.clone(),
            friendly_name: disk_id.clone(),
            size_bytes: 0,
            removable: false,
            is_system_disk: false,
            partitions: Vec::new(),
        });

        let partition = Partition {
            id: device_name,
            label: None,
            fs: Some(mount.fs_type.clone()),
            size_bytes: mount.size_bytes,
            mount_points: vec![mount.mount_point.clone()],
        };
        entry.size_bytes = entry.size_bytes.saturating_add(mount.size_bytes);
        if mount.mount_point == "/" {
            entry.is_system_disk = true;
        }
        if mount.mount_point.starts_with("/Volumes/") {
            entry.removable = true;
        }
        entry.partitions.push(partition);
    }

    Ok(disks.into_values().collect())
}

#[cfg(target_os = "macos")]
#[derive(Debug, Clone)]
struct MountEntry {
    device: String,
    mount_point: String,
    fs_type: String,
    size_bytes: u64,
}

#[cfg(target_os = "macos")]
fn read_mounts() -> Result<Vec<MountEntry>> {
    use libc::{getfsstat, statfs, MNT_NOWAIT};
    use std::ffi::CStr;
    use std::mem::size_of;
    use std::ptr;

    let count = unsafe { getfsstat(ptr::null_mut(), 0, MNT_NOWAIT) };
    if count < 0 {
        return Err(anyhow!("getfsstat failed"));
    }
    let mut buf = vec![unsafe { std::mem::zeroed::<statfs>() }; count as usize];
    let res = unsafe {
        getfsstat(
            buf.as_mut_ptr(),
            (buf.len() * size_of::<statfs>()) as i32,
            MNT_NOWAIT,
        )
    };
    if res < 0 {
        return Err(anyhow!("getfsstat returned error"));
    }

    let mut entries = Vec::new();
    for entry in buf.into_iter().take(res as usize) {
        let device = unsafe { CStr::from_ptr(entry.f_mntfromname.as_ptr()) }
            .to_string_lossy()
            .to_string();
        let mount_point = unsafe { CStr::from_ptr(entry.f_mntonname.as_ptr()) }
            .to_string_lossy()
            .to_string();
        let fs_type = unsafe { CStr::from_ptr(entry.f_fstypename.as_ptr()) }
            .to_string_lossy()
            .to_string();
        let size_bytes = (entry.f_blocks as u64).saturating_mul(entry.f_bsize as u64);
        entries.push(MountEntry {
            device,
            mount_point,
            fs_type,
            size_bytes,
        });
    }
    Ok(entries)
}

#[cfg(target_os = "macos")]
fn split_disk_id(device_name: &str) -> String {
    if device_name.starts_with("disk") {
        if let Some(idx) = device_name.find('s') {
            return device_name[..idx].to_string();
        }
    }
    device_name.to_string()
}

#[cfg(target_os = "macos")]
fn read_os_version() -> String {
    sysctl_string("kern.osproductversion")
        .or_else(|| sysctl_string("kern.osrelease"))
        .unwrap_or_else(|| "unknown".to_string())
}

#[cfg(target_os = "macos")]
fn read_machine() -> String {
    sysctl_string("hw.model")
        .or_else(|| sysctl_string("kern.hostname"))
        .unwrap_or_else(|| "unknown".to_string())
}

#[cfg(target_os = "macos")]
fn sysctl_string(name: &str) -> Option<String> {
    use libc::sysctlbyname;
    use std::ffi::CString;
    use std::ptr;

    let c_name = CString::new(name).ok()?;
    let mut size = 0usize;
    let res = unsafe { sysctlbyname(c_name.as_ptr(), ptr::null_mut(), &mut size, ptr::null_mut(), 0) };
    if res != 0 || size == 0 {
        return None;
    }

    let mut buffer = vec![0u8; size];
    let res = unsafe {
        sysctlbyname(
            c_name.as_ptr(),
            buffer.as_mut_ptr() as *mut _,
            &mut size,
            ptr::null_mut(),
            0,
        )
    };
    if res != 0 {
        return None;
    }
    if let Some(0) = buffer.last().copied() {
        buffer.pop();
    }
    String::from_utf8(buffer).ok()
}
