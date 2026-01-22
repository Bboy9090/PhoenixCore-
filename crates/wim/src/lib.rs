use anyhow::{anyhow, Result};
use std::path::Path;

#[derive(Debug, Clone)]
pub struct WimImageInfo {
    pub index: u32,
    pub name: Option<String>,
    pub description: Option<String>,
    pub total_bytes: Option<u64>,
}

#[cfg(windows)]
mod windows_impl {
    use super::WimImageInfo;
    use anyhow::{anyhow, Result};
    use std::ffi::c_void;
    use std::path::Path;
    use std::ptr;
    use windows::core::PCWSTR;
    use windows::Win32::Foundation::{BOOL, HANDLE, INVALID_HANDLE_VALUE};

    const WIM_GENERIC_READ: u32 = 0x80000000;
    const WIM_OPEN_EXISTING: u32 = 3;
    const WIM_FLAG_SHARE_READ: u32 = 0x00000001;
    const WIM_FLAG_SHARE_WRITE: u32 = 0x00000002;
    const WIM_COMPRESS_NONE: u32 = 0;

    #[link(name = "wimgapi")]
    extern "system" {
        fn WIMCreateFile(
            path: PCWSTR,
            desired_access: u32,
            creation_disposition: u32,
            flags_and_attributes: u32,
            compression_type: u32,
            creation_result: *mut u32,
        ) -> HANDLE;
        fn WIMCloseHandle(handle: HANDLE) -> BOOL;
        fn WIMGetImageCount(handle: HANDLE, count: *mut u32) -> BOOL;
        fn WIMLoadImage(handle: HANDLE, index: u32) -> HANDLE;
        fn WIMGetImageInformation(
            handle: HANDLE,
            info: *mut *mut c_void,
            size: *mut u32,
        ) -> BOOL;
        fn WIMFreeMemory(ptr: *mut c_void);
        fn WIMApplyImage(handle: HANDLE, path: PCWSTR, flags: u32) -> BOOL;
    }

    pub fn list_images(path: &Path) -> Result<Vec<WimImageInfo>> {
        let handle = open_wim_file(path)?;
        let count = get_image_count(handle)?;
        let mut images = Vec::new();

        for index in 1..=count {
            let image_handle = unsafe { WIMLoadImage(handle, index) };
            if image_handle == INVALID_HANDLE_VALUE {
                continue;
            }

            let xml = get_image_information(image_handle)?;
            let name = extract_tag(&xml, "NAME");
            let description = extract_tag(&xml, "DESCRIPTION");
            let total_bytes = extract_tag(&xml, "TOTALBYTES")
                .and_then(|value| value.parse::<u64>().ok());

            unsafe {
                WIMCloseHandle(image_handle);
            }

            images.push(WimImageInfo {
                index,
                name,
                description,
                total_bytes,
            });
        }

        unsafe {
            WIMCloseHandle(handle);
        }

        Ok(images)
    }

    pub fn apply_image(path: &Path, index: u32, target_dir: &Path) -> Result<()> {
        if !target_dir.is_dir() {
            return Err(anyhow!("target dir does not exist"));
        }

        let handle = open_wim_file(path)?;
        let image_handle = unsafe { WIMLoadImage(handle, index) };
        if image_handle == INVALID_HANDLE_VALUE {
            unsafe { WIMCloseHandle(handle) };
            return Err(anyhow!("failed to load image {}", index));
        }

        let wide = wide(target_dir);
        let ok = unsafe { WIMApplyImage(image_handle, PCWSTR(wide.as_ptr()), 0) };

        unsafe {
            WIMCloseHandle(image_handle);
            WIMCloseHandle(handle);
        }

        if ok.as_bool() {
            Ok(())
        } else {
            Err(anyhow!("WIMApplyImage failed"))
        }
    }

    fn open_wim_file(path: &Path) -> Result<HANDLE> {
        let wide = wide(path);
        let mut creation_result = 0u32;
        let handle = unsafe {
            WIMCreateFile(
                PCWSTR(wide.as_ptr()),
                WIM_GENERIC_READ,
                WIM_OPEN_EXISTING,
                WIM_FLAG_SHARE_READ | WIM_FLAG_SHARE_WRITE,
                WIM_COMPRESS_NONE,
                &mut creation_result,
            )
        };

        if handle == INVALID_HANDLE_VALUE {
            return Err(anyhow!("WIMCreateFile failed"));
        }

        Ok(handle)
    }

    fn get_image_count(handle: HANDLE) -> Result<u32> {
        let mut count = 0u32;
        let ok = unsafe { WIMGetImageCount(handle, &mut count) };
        if ok.as_bool() {
            Ok(count)
        } else {
            Err(anyhow!("WIMGetImageCount failed"))
        }
    }

    fn get_image_information(handle: HANDLE) -> Result<String> {
        let mut ptr: *mut c_void = ptr::null_mut();
        let mut size = 0u32;
        let ok = unsafe { WIMGetImageInformation(handle, &mut ptr, &mut size) };
        if !ok.as_bool() || ptr.is_null() || size == 0 {
            return Err(anyhow!("WIMGetImageInformation failed"));
        }

        let bytes = unsafe { std::slice::from_raw_parts(ptr as *const u8, size as usize) };
        let xml = String::from_utf8_lossy(bytes).to_string();
        unsafe {
            WIMFreeMemory(ptr);
        }
        Ok(xml)
    }

    fn extract_tag(xml: &str, tag: &str) -> Option<String> {
        let start_tag = format!("<{}>", tag);
        let end_tag = format!("</{}>", tag);
        let start = xml.find(&start_tag)? + start_tag.len();
        let end = xml[start..].find(&end_tag)? + start;
        let value = xml[start..end].trim();
        if value.is_empty() {
            None
        } else {
            Some(value.to_string())
        }
    }

    fn wide(path: &Path) -> Vec<u16> {
        use std::os::windows::prelude::*;
        path.as_os_str()
            .encode_wide()
            .chain(std::iter::once(0))
            .collect()
    }
}

#[cfg(windows)]
pub fn list_images(path: impl AsRef<Path>) -> Result<Vec<WimImageInfo>> {
    windows_impl::list_images(path.as_ref())
}

#[cfg(not(windows))]
pub fn list_images(_path: impl AsRef<Path>) -> Result<Vec<WimImageInfo>> {
    Err(anyhow!("WIM operations require Windows"))
}

#[cfg(windows)]
pub fn apply_image(path: impl AsRef<Path>, index: u32, target_dir: impl AsRef<Path>) -> Result<()> {
    windows_impl::apply_image(path.as_ref(), index, target_dir.as_ref())
}

#[cfg(not(windows))]
pub fn apply_image(_path: impl AsRef<Path>, _index: u32, _target_dir: impl AsRef<Path>) -> Result<()> {
    Err(anyhow!("WIM operations require Windows"))
}
