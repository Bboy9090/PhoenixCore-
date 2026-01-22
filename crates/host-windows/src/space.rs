use anyhow::{anyhow, Result};
use windows::core::PCWSTR;
use windows::Win32::Storage::FileSystem::GetDiskFreeSpaceExW;

pub fn free_space_bytes(path: &str) -> Result<u64> {
    let wide = wide(path);
    let mut free = 0u64;
    let mut total = 0u64;
    let mut total_free = 0u64;
    let ok = unsafe {
        GetDiskFreeSpaceExW(
            PCWSTR(wide.as_ptr()),
            Some(&mut free),
            Some(&mut total),
            Some(&mut total_free),
        )
    };
    if ok.as_bool() {
        Ok(free)
    } else {
        Err(anyhow!("GetDiskFreeSpaceExW failed"))
    }
}

fn wide(s: &str) -> Vec<u16> {
    use std::os::windows::prelude::*;
    std::ffi::OsStr::new(s)
        .encode_wide()
        .chain(std::iter::once(0))
        .collect()
}
