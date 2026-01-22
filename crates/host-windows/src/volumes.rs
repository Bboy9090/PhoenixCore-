use anyhow::{anyhow, Result};
use std::ffi::c_void;

use windows::core::PCWSTR;
use windows::Win32::Foundation::{CloseHandle, HANDLE, INVALID_HANDLE_VALUE};
use windows::Win32::Storage::FileSystem::{
    CreateFileW, GetDiskFreeSpaceExW, GetLogicalDrives, GetVolumeInformationW,
    FILE_ATTRIBUTE_NORMAL, FILE_GENERIC_READ, FILE_SHARE_READ, FILE_SHARE_WRITE, OPEN_EXISTING,
};
use windows::Win32::System::Ioctl::{
    DeviceIoControl, IOCTL_VOLUME_GET_VOLUME_DISK_EXTENTS, VOLUME_DISK_EXTENTS,
};
use windows::Win32::System::SystemInformation::GetWindowsDirectoryW;

#[derive(Debug, Clone)]
pub struct VolumeMount {
    pub id: String,
    pub label: Option<String>,
    pub fs: Option<String>,
    pub size_bytes: u64,
    pub mount_points: Vec<String>,
    pub disk_number: u32,
    pub offset_bytes: u64,
    pub length_bytes: u64,
}

fn wide(s: &str) -> Vec<u16> {
    use std::os::windows::prelude::*;
    std::ffi::OsStr::new(s)
        .encode_wide()
        .chain(std::iter::once(0))
        .collect()
}

fn open_volume_handle(drive_letter: char) -> Result<HANDLE> {
    let path = format!(r"\\.\{}:", drive_letter);
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

pub fn system_drive_letter() -> Result<String> {
    unsafe {
        let mut buf = [0u16; 260];
        let len = GetWindowsDirectoryW(Some(&mut buf)) as usize;
        if len == 0 {
            return Err(anyhow!("GetWindowsDirectoryW failed"));
        }
        let s = String::from_utf16_lossy(&buf[..len]);
        let drive = s.chars().take(3).collect::<String>();
        Ok(drive.to_ascii_uppercase())
    }
}

fn list_logical_drive_letters() -> Vec<char> {
    unsafe {
        let mask = GetLogicalDrives();
        let mut letters = Vec::new();
        for (idx, letter) in ('A'..='Z').enumerate() {
            if mask & (1u32 << idx) != 0 {
                letters.push(letter);
            }
        }
        letters
    }
}

fn get_volume_info(root: &str) -> Result<(Option<String>, Option<String>)> {
    let wroot = wide(root);
    let mut name_buf = [0u16; 256];
    let mut fs_buf = [0u16; 256];

    unsafe {
        let ok = GetVolumeInformationW(
            PCWSTR(wroot.as_ptr()),
            Some(&mut name_buf),
            None,
            None,
            None,
            Some(&mut fs_buf),
        );
        if !ok.as_bool() {
            return Err(anyhow!("GetVolumeInformationW failed for {}", root));
        }
    }

    let label = String::from_utf16_lossy(&name_buf)
        .trim_end_matches('\0')
        .trim()
        .to_string();
    let fs = String::from_utf16_lossy(&fs_buf)
        .trim_end_matches('\0')
        .trim()
        .to_string();

    let label = if label.is_empty() { None } else { Some(label) };
    let fs = if fs.is_empty() { None } else { Some(fs) };

    Ok((label, fs))
}

fn get_volume_size(root: &str) -> Result<u64> {
    let wroot = wide(root);
    let mut free = 0u64;
    let mut total = 0u64;
    let mut total_free = 0u64;

    unsafe {
        let ok = GetDiskFreeSpaceExW(
            PCWSTR(wroot.as_ptr()),
            Some(&mut free),
            Some(&mut total),
            Some(&mut total_free),
        );
        if !ok.as_bool() {
            return Err(anyhow!("GetDiskFreeSpaceExW failed for {}", root));
        }
    }

    Ok(total)
}

fn volume_extent_for_drive(drive_letter: char) -> Result<(u32, u64, u64)> {
    let handle = open_volume_handle(drive_letter)?;
    let mut out = [0u8; 1024];
    let mut returned = 0u32;

    unsafe {
        let ok = DeviceIoControl(
            handle,
            IOCTL_VOLUME_GET_VOLUME_DISK_EXTENTS,
            None,
            0,
            Some(out.as_mut_ptr() as *mut c_void),
            out.len() as u32,
            Some(&mut returned),
            None,
        );
        CloseHandle(handle);

        if !ok.as_bool() {
            return Err(anyhow!(
                "IOCTL_VOLUME_GET_VOLUME_DISK_EXTENTS failed for {}:",
                drive_letter
            ));
        }
    }

    if out.len() < std::mem::size_of::<VOLUME_DISK_EXTENTS>() {
        return Err(anyhow!("Extent buffer too small"));
    }

    let extents: VOLUME_DISK_EXTENTS =
        unsafe { std::ptr::read_unaligned(out.as_ptr() as *const _) };
    if extents.NumberOfDiskExtents == 0 {
        return Err(anyhow!("No extents for {}:", drive_letter));
    }

    let extent = extents.Extents[0];
    let offset = (extent.StartingOffset as i64).max(0) as u64;
    let length = (extent.ExtentLength as i64).max(0) as u64;
    Ok((extent.DiskNumber, offset, length))
}

pub fn enumerate_volume_mounts() -> Result<Vec<VolumeMount>> {
    let mut mounts = Vec::new();

    for letter in list_logical_drive_letters() {
        let root = format!("{}:\\", letter);

        let (label, fs) = match get_volume_info(&root) {
            Ok(value) => value,
            Err(_) => continue,
        };

        let size_bytes = get_volume_size(&root).unwrap_or(0);

        let (disk_number, offset_bytes, length_bytes) =
            match volume_extent_for_drive(letter) {
                Ok(value) => value,
                Err(_) => continue,
            };

        let volume_id = format!("Drive{}", letter);
        mounts.push(VolumeMount {
            id: volume_id,
            label,
            fs,
            size_bytes,
            mount_points: vec![root],
            disk_number,
            offset_bytes,
            length_bytes,
        });
    }

    Ok(mounts)
}
