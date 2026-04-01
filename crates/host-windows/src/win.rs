use anyhow::{anyhow, Result};
use phoenix_core::Disk;
use std::ffi::c_void;
use std::mem::size_of;

use windows::core::PCWSTR;
use windows::Win32::Foundation::{CloseHandle, HANDLE, INVALID_HANDLE_VALUE};
use windows::Win32::Storage::FileSystem::{
    CreateFileW, FILE_ATTRIBUTE_NORMAL, FILE_GENERIC_READ, FILE_SHARE_READ, FILE_SHARE_WRITE,
    OPEN_EXISTING,
};
use windows::Win32::System::Ioctl::{
    DeviceIoControl, DRIVE_LAYOUT_INFORMATION_EX, IOCTL_DISK_GET_DRIVE_GEOMETRY_EX,
    IOCTL_DISK_GET_DRIVE_LAYOUT_EX, IOCTL_STORAGE_QUERY_PROPERTY, PARTITION_INFORMATION_EX,
    STORAGE_PROPERTY_QUERY, StorageDeviceProperty, STORAGE_QUERY_TYPE,
};
use windows::Win32::System::SystemInformation::{GetComputerNameW, GetVersionExW, OSVERSIONINFOW};

fn wide(s: &str) -> Vec<u16> {
    use std::os::windows::prelude::*;
    std::ffi::OsStr::new(s)
        .encode_wide()
        .chain(std::iter::once(0))
        .collect()
}

fn open_physical_drive(n: u32) -> Result<HANDLE> {
    let path = format!(r"\\.\PhysicalDrive{}", n);
    let w = wide(&path);

    unsafe {
        let handle = CreateFileW(
            PCWSTR(w.as_ptr()),
            FILE_GENERIC_READ,
            FILE_SHARE_READ | FILE_SHARE_WRITE,
            None,
            OPEN_EXISTING,
            FILE_ATTRIBUTE_NORMAL,
            None,
        );

        if handle == INVALID_HANDLE_VALUE {
            return Err(anyhow!("CreateFileW failed for {}", path));
        }

        Ok(handle)
    }
}

fn query_size_bytes(handle: HANDLE) -> Result<u64> {
    let mut out = [0u8; 1024];
    let mut returned = 0u32;

    unsafe {
        let ok = DeviceIoControl(
            handle,
            IOCTL_DISK_GET_DRIVE_GEOMETRY_EX,
            None,
            0,
            Some(out.as_mut_ptr() as *mut c_void),
            out.len() as u32,
            Some(&mut returned),
            None,
        );

        if !ok.as_bool() {
            return Err(anyhow!("IOCTL_DISK_GET_DRIVE_GEOMETRY_EX failed"));
        }
    }

    if out.len() < 32 {
        return Err(anyhow!("Geometry buffer too small"));
    }

    let disk_size = i64::from_le_bytes(out[24..32].try_into().unwrap());
    Ok(disk_size.max(0) as u64)
}

fn query_friendly_and_removable(handle: HANDLE) -> Result<(String, bool)> {
    let mut query = STORAGE_PROPERTY_QUERY {
        PropertyId: StorageDeviceProperty,
        QueryType: STORAGE_QUERY_TYPE(0),
        AdditionalParameters: [0],
    };

    let mut out = [0u8; 4096];
    let mut returned = 0u32;

    unsafe {
        let ok = DeviceIoControl(
            handle,
            IOCTL_STORAGE_QUERY_PROPERTY,
            Some(&query as *const _ as *const c_void),
            size_of::<STORAGE_PROPERTY_QUERY>() as u32,
            Some(out.as_mut_ptr() as *mut c_void),
            out.len() as u32,
            Some(&mut returned),
            None,
        );

        if !ok.as_bool() {
            return Ok(("Unknown Disk".to_string(), false));
        }
    }

    let removable = out.get(8).copied().unwrap_or(0) != 0;
    let vendor_slice = out.get(12..16).unwrap_or(&[0, 0, 0, 0]);
    let prod_slice = out.get(16..20).unwrap_or(&[0, 0, 0, 0]);
    let vendor_off = u32::from_le_bytes(vendor_slice.try_into().unwrap_or([0; 4])) as usize;
    let prod_off = u32::from_le_bytes(prod_slice.try_into().unwrap_or([0; 4])) as usize;

    fn read_cstr(buf: &[u8], off: usize) -> Option<String> {
        if off == 0 || off >= buf.len() {
            return None;
        }
        let tail = &buf[off..];
        let end = tail.iter().position(|&b| b == 0).unwrap_or(tail.len());
        let s = String::from_utf8_lossy(&tail[..end]).trim().to_string();
        if s.is_empty() { None } else { Some(s) }
    }

    let vendor = read_cstr(&out, vendor_off).unwrap_or_default();
    let product = read_cstr(&out, prod_off).unwrap_or_default();
    let name = format!("{} {}", vendor, product).trim().to_string();
    let name = if name.is_empty() { "Unknown Disk".to_string() } else { name };

    Ok((name, removable))
}

pub fn os_version_string() -> String {
    unsafe {
        let mut info = OSVERSIONINFOW::default();
        info.dwOSVersionInfoSize = size_of::<OSVERSIONINFOW>() as u32;
        if GetVersionExW(&mut info).as_bool() {
            return format!(
                "{}.{}.{}",
                info.dwMajorVersion, info.dwMinorVersion, info.dwBuildNumber
            );
        }
    }
    "unknown".to_string()
}

pub fn machine_name_string() -> String {
    unsafe {
        let mut buf = [0u16; 256];
        let mut size = buf.len() as u32;
        if GetComputerNameW(&mut buf, &mut size).as_bool() {
            return String::from_utf16_lossy(&buf[..size as usize]);
        }
    }
    "unknown".to_string()
}

pub fn enumerate_physical_disks() -> Result<Vec<Disk>> {
    let mut disks = Vec::new();

    for n in 0..32u32 {
        let handle = match open_physical_drive(n) {
            Ok(handle) => handle,
            Err(_) => continue,
        };

        let size_bytes = query_size_bytes(handle).unwrap_or(0);
        let (friendly, removable) = query_friendly_and_removable(handle)
            .unwrap_or(("Unknown Disk".to_string(), false));

        unsafe {
            CloseHandle(handle);
        }

        disks.push(Disk {
            id: format!("PhysicalDrive{}", n),
            friendly_name: friendly,
            size_bytes,
            removable,
            is_system_disk: false,
            partitions: Vec::new(),
        });
    }

    if disks.is_empty() {
        return Err(anyhow!("No disks detected (CreateFileW scan found none)"));
    }

    Ok(disks)
}

#[derive(Debug, Clone)]
pub struct PartitionEntry {
    pub number: u32,
    pub offset_bytes: u64,
    pub length_bytes: u64,
}

pub fn enumerate_partitions(disk_number: u32) -> Result<Vec<PartitionEntry>> {
    let handle = open_physical_drive(disk_number)?;
    let mut buffer = vec![0u8; 64 * 1024];
    let mut returned = 0u32;

    unsafe {
        let ok = DeviceIoControl(
            handle,
            IOCTL_DISK_GET_DRIVE_LAYOUT_EX,
            None,
            0,
            Some(buffer.as_mut_ptr() as *mut c_void),
            buffer.len() as u32,
            Some(&mut returned),
            None,
        );
        CloseHandle(handle);

        if !ok.as_bool() {
            return Err(anyhow!("IOCTL_DISK_GET_DRIVE_LAYOUT_EX failed"));
        }
    }

    if buffer.len() < std::mem::size_of::<DRIVE_LAYOUT_INFORMATION_EX>() {
        return Err(anyhow!("Drive layout buffer too small"));
    }

    let layout = unsafe { &*(buffer.as_ptr() as *const DRIVE_LAYOUT_INFORMATION_EX) };
    let count = layout.PartitionCount as usize;
    let first = layout.PartitionEntry.as_ptr();
    let mut partitions = Vec::new();

    for idx in 0..count {
        let entry: PARTITION_INFORMATION_EX =
            unsafe { *first.add(idx) };
        if entry.PartitionNumber == 0 {
            continue;
        }

        let offset = (entry.StartingOffset as i64).max(0) as u64;
        let length = (entry.PartitionLength as i64).max(0) as u64;
        if length == 0 {
            continue;
        }

        partitions.push(PartitionEntry {
            number: entry.PartitionNumber,
            offset_bytes: offset,
            length_bytes: length,
        });
    }

    Ok(partitions)
}
