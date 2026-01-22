use anyhow::{anyhow, Result};

#[derive(Debug, Clone, Copy)]
pub enum FileSystem {
    Fat32,
    Ntfs,
    ExFat,
}

pub fn parse_filesystem(_value: &str) -> Option<FileSystem> {
    match _value.trim().to_ascii_lowercase().as_str() {
        "fat32" => Some(FileSystem::Fat32),
        "ntfs" => Some(FileSystem::Ntfs),
        "exfat" => Some(FileSystem::ExFat),
        _ => None,
    }
}

pub fn logical_drive_letters() -> Vec<char> {
    Vec::new()
}

pub fn prepare_usb_disk(
    _disk_number: u32,
    _disk_size: u64,
    _fs: FileSystem,
    _label: Option<&str>,
) -> Result<char> {
    Err(anyhow!("phoenix-host-windows format requires Windows"))
}

pub fn format_existing_volume(
    _drive_letter: char,
    _fs: FileSystem,
    _label: Option<&str>,
) -> Result<()> {
    Err(anyhow!("phoenix-host-windows format requires Windows"))
}
