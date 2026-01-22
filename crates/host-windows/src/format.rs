use anyhow::{anyhow, Result};
use std::collections::HashSet;
use std::ffi::c_void;
use std::sync::atomic::{AtomicI8, Ordering};
use std::time::{Duration, Instant};

use windows::core::{GUID, PCSTR, PCWSTR};
use windows::Win32::Foundation::{CloseHandle, BOOL, HANDLE, INVALID_HANDLE_VALUE};
use windows::Win32::Storage::FileSystem::{
    CreateFileW, GetLogicalDrives, FILE_ATTRIBUTE_NORMAL, FILE_GENERIC_READ, FILE_GENERIC_WRITE,
    FILE_SHARE_READ, FILE_SHARE_WRITE, OPEN_EXISTING,
};
use windows::Win32::Storage::Ioctl::{
    CREATE_DISK, CREATE_DISK_GPT, DRIVE_LAYOUT_INFORMATION_EX, DRIVE_LAYOUT_INFORMATION_GPT,
    IOCTL_DISK_CREATE_DISK, IOCTL_DISK_SET_DRIVE_LAYOUT_EX, IOCTL_DISK_UPDATE_PROPERTIES,
    PARTITION_INFORMATION_EX, PARTITION_INFORMATION_GPT, PARTITION_STYLE_GPT,
};
use windows::Win32::System::Ioctl::DeviceIoControl;
use windows::Win32::System::LibraryLoader::{FreeLibrary, GetProcAddress, LoadLibraryW};
use uuid::Uuid;

const FMIFS_DONE: u32 = 0;
const FMIFS_HARDDISK: u32 = 0x0C;
static FORMAT_RESULT: AtomicI8 = AtomicI8::new(-1);

pub enum FileSystem {
    Fat32,
    Ntfs,
    ExFat,
}

impl FileSystem {
    pub fn as_str(&self) -> &'static str {
        match self {
            FileSystem::Fat32 => "FAT32",
            FileSystem::Ntfs => "NTFS",
            FileSystem::ExFat => "exFAT",
        }
    }
}

pub fn parse_filesystem(value: &str) -> Option<FileSystem> {
    match value.trim().to_ascii_lowercase().as_str() {
        "fat32" => Some(FileSystem::Fat32),
        "ntfs" => Some(FileSystem::Ntfs),
        "exfat" => Some(FileSystem::ExFat),
        _ => None,
    }
}

pub fn logical_drive_letters() -> Vec<char> {
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

pub fn prepare_usb_disk(
    disk_number: u32,
    disk_size: u64,
    fs: FileSystem,
    label: Option<&str>,
) -> Result<char> {
    let before = logical_drive_letters();
    create_single_gpt_partition(disk_number, disk_size, label)?;
    let letter = wait_for_new_drive_letter(&before, Duration::from_secs(15))?;
    format_volume(letter, fs, label, true)?;
    Ok(letter)
}

pub fn format_existing_volume(
    drive_letter: char,
    fs: FileSystem,
    label: Option<&str>,
) -> Result<()> {
    format_volume(drive_letter, fs, label, true)
}

fn wait_for_new_drive_letter(before: &[char], timeout: Duration) -> Result<char> {
    let before_set: HashSet<char> = before.iter().copied().collect();
    let start = Instant::now();
    loop {
        let now = logical_drive_letters();
        for letter in now {
            if !before_set.contains(&letter) {
                return Ok(letter);
            }
        }
        if start.elapsed() > timeout {
            return Err(anyhow!("timed out waiting for new volume mount"));
        }
        std::thread::sleep(Duration::from_millis(300));
    }
}

fn create_single_gpt_partition(disk_number: u32, disk_size: u64, label: Option<&str>) -> Result<()> {
    let handle = open_physical_drive_rw(disk_number)?;
    let disk_id = GUID::from_u128(Uuid::new_v4().as_u128());
    initialize_gpt(handle, disk_id)?;

    let alignment = 1 * 1024 * 1024u64;
    let usable = disk_size.saturating_sub(alignment * 2);
    if usable == 0 {
        unsafe { CloseHandle(handle) };
        return Err(anyhow!("disk too small for partitioning"));
    }

    let mut layout: DRIVE_LAYOUT_INFORMATION_EX = unsafe { std::mem::zeroed() };
    layout.PartitionStyle = PARTITION_STYLE_GPT;
    layout.PartitionCount = 1;
    unsafe {
        layout.Anonymous.Gpt = DRIVE_LAYOUT_INFORMATION_GPT {
            DiskId: disk_id,
            StartingUsableOffset: alignment as i64,
            UsableLength: usable as i64,
            MaxPartitionCount: 128,
        };
    }

    let partition_id = GUID::from_u128(Uuid::new_v4().as_u128());
    let mut entry: PARTITION_INFORMATION_EX = unsafe { std::mem::zeroed() };
    entry.PartitionStyle = PARTITION_STYLE_GPT;
    entry.StartingOffset = alignment as i64;
    entry.PartitionLength = usable as i64;
    entry.PartitionNumber = 1;
    entry.RewritePartition = BOOL(1);
    unsafe {
        entry.Anonymous.Gpt = PARTITION_INFORMATION_GPT {
            PartitionType: GUID::from_u128(0xEBD0A0A2_B9E5_4433_87C0_68B6B72699C7),
            PartitionId: partition_id,
            Attributes: 0,
            Name: gpt_name_from_label(label),
        };
        layout.PartitionEntry[0] = entry;
    }

    unsafe {
        let ok = DeviceIoControl(
            handle,
            IOCTL_DISK_SET_DRIVE_LAYOUT_EX,
            Some(&layout as *const _ as *const c_void),
            std::mem::size_of::<DRIVE_LAYOUT_INFORMATION_EX>() as u32,
            None,
            0,
            None,
            None,
        );
        if !ok.as_bool() {
            CloseHandle(handle);
            return Err(anyhow!("IOCTL_DISK_SET_DRIVE_LAYOUT_EX failed"));
        }

        let ok = DeviceIoControl(
            handle,
            IOCTL_DISK_UPDATE_PROPERTIES,
            None,
            0,
            None,
            0,
            None,
            None,
        );
        if !ok.as_bool() {
            CloseHandle(handle);
            return Err(anyhow!("IOCTL_DISK_UPDATE_PROPERTIES failed"));
        }
    }

    unsafe { CloseHandle(handle) };
    Ok(())
}

fn initialize_gpt(handle: HANDLE, disk_id: GUID) -> Result<()> {
    let mut create: CREATE_DISK = unsafe { std::mem::zeroed() };
    create.PartitionStyle = PARTITION_STYLE_GPT;
    unsafe {
        create.Anonymous.Gpt = CREATE_DISK_GPT {
            DiskId: disk_id,
            MaxPartitionCount: 128,
        };
    }

    unsafe {
        let ok = DeviceIoControl(
            handle,
            IOCTL_DISK_CREATE_DISK,
            Some(&create as *const _ as *const c_void),
            std::mem::size_of::<CREATE_DISK>() as u32,
            None,
            0,
            None,
            None,
        );
        if !ok.as_bool() {
            return Err(anyhow!("IOCTL_DISK_CREATE_DISK failed"));
        }
    }
    Ok(())
}

fn format_volume(drive_letter: char, fs: FileSystem, label: Option<&str>, quick: bool) -> Result<()> {
    FORMAT_RESULT.store(-1, Ordering::SeqCst);

    let module = unsafe { LoadLibraryW(PCWSTR(wide("fmifs.dll").as_ptr())) };
    if module.0 == 0 {
        return Err(anyhow!("failed to load fmifs.dll"));
    }

    let proc = unsafe { GetProcAddress(module, PCSTR(b"FormatEx\0".as_ptr())) };
    if proc.is_none() {
        unsafe { FreeLibrary(module) };
        return Err(anyhow!("FormatEx not found in fmifs.dll"));
    }

    let format_ex: FormatExFn = unsafe { std::mem::transmute(proc) };
    let drive_root = format!("{}:\\", drive_letter);
    let fs_name = fs.as_str().to_string();
    let label = label.unwrap_or("PHOENIX");

    unsafe {
        format_ex(
            PCWSTR(wide(&drive_root).as_ptr()),
            FMIFS_HARDDISK,
            PCWSTR(wide(&fs_name).as_ptr()),
            PCWSTR(wide(label).as_ptr()),
            BOOL(if quick { 1 } else { 0 }),
            0,
            Some(format_callback),
        );
        FreeLibrary(module);
    }

    match FORMAT_RESULT.load(Ordering::SeqCst) {
        1 => Ok(()),
        0 => Err(anyhow!("format failed")),
        _ => Err(anyhow!("format did not report completion")),
    }
}

fn open_physical_drive_rw(n: u32) -> Result<HANDLE> {
    let path = format!(r"\\.\PhysicalDrive{}", n);
    let w = wide(&path);

    unsafe {
        let handle = CreateFileW(
            PCWSTR(w.as_ptr()),
            FILE_GENERIC_READ | FILE_GENERIC_WRITE,
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

unsafe extern "system" fn format_callback(
    command: u32,
    _subcommand: u32,
    data: *mut c_void,
) -> u32 {
    if command == FMIFS_DONE {
        if data.is_null() {
            FORMAT_RESULT.store(0, Ordering::SeqCst);
        } else {
            let success = *(data as *const i32) != 0;
            FORMAT_RESULT.store(if success { 1 } else { 0 }, Ordering::SeqCst);
        }
    }
    1
}

fn wide(s: &str) -> Vec<u16> {
    use std::os::windows::prelude::*;
    std::ffi::OsStr::new(s)
        .encode_wide()
        .chain(std::iter::once(0))
        .collect()
}

fn gpt_name_from_label(label: Option<&str>) -> [u16; 36] {
    let mut name = [0u16; 36];
    let value = label.unwrap_or("PHOENIX");
    let mut iter = value.encode_utf16();
    for slot in name.iter_mut() {
        if let Some(ch) = iter.next() {
            *slot = ch;
        } else {
            break;
        }
    }
    name
}
