use anyhow::{anyhow, Result};
use phoenix_core::WorkflowDefinition;
use std::path::{Path, PathBuf};

#[derive(Debug, Clone, serde::Serialize, serde::Deserialize)]
pub struct PackManifest {
    pub schema_version: String,
    pub name: String,
    pub version: String,
    pub description: Option<String>,
    pub workflows: Vec<String>,
    pub assets: Option<String>,
}

pub fn load_pack_manifest(path: impl AsRef<Path>) -> Result<PackManifest> {
    let path = path.as_ref();
    let data = std::fs::read_to_string(path)?;
    let manifest: PackManifest = serde_json::from_str(&data)?;
    Ok(manifest)
}

pub fn resolve_pack_workflows(
    manifest_path: impl AsRef<Path>,
) -> Result<Vec<(PathBuf, WorkflowDefinition)>> {
    let manifest_path = manifest_path.as_ref();
    let manifest = load_pack_manifest(manifest_path)?;
    let base = manifest_path
        .parent()
        .ok_or_else(|| anyhow!("pack manifest has no parent directory"))?;
    let mut workflows = Vec::new();
    for workflow_path in &manifest.workflows {
        let path = base.join(workflow_path);
        let data = std::fs::read_to_string(&path)?;
        let workflow: WorkflowDefinition = serde_json::from_str(&data)?;
        workflows.push((path, workflow));
    }
    Ok(workflows)
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum SourceKind {
    Directory,
    Iso,
}

pub struct PreparedSource {
    pub root: PathBuf,
    pub kind: SourceKind,
    _mount: Option<IsoMount>,
}

pub fn prepare_source(path: impl AsRef<Path>) -> Result<PreparedSource> {
    let path = path.as_ref();
    if path.is_dir() {
        let root = path.canonicalize().unwrap_or_else(|_| path.to_path_buf());
        return Ok(PreparedSource {
            root,
            kind: SourceKind::Directory,
            _mount: None,
        });
    }

    if is_iso(path) {
        return mount_iso(path);
    }

    Err(anyhow!("unsupported source path"))
}

pub fn find_windows_image(root: impl AsRef<Path>) -> Result<PathBuf> {
    let root = root.as_ref();
    let candidates = [
        root.join("sources").join("install.wim"),
        root.join("sources").join("install.esd"),
        root.join("install.wim"),
        root.join("install.esd"),
    ];

    for candidate in candidates {
        if candidate.is_file() {
            return Ok(candidate);
        }
    }

    Err(anyhow!("install.wim or install.esd not found in source"))
}

pub fn resolve_windows_image(path: impl AsRef<Path>) -> Result<(PathBuf, Option<PreparedSource>)> {
    let path = path.as_ref();
    if path.is_file() {
        if is_wim(path) {
            return Ok((path.to_path_buf(), None));
        }
        return Err(anyhow!("unsupported image file type"));
    }

    let prepared = prepare_source(path)?;
    let wim_path = find_windows_image(&prepared.root)?;
    Ok((wim_path, Some(prepared)))
}

fn is_iso(path: &Path) -> bool {
    path.extension()
        .and_then(|ext| ext.to_str())
        .map(|ext| ext.eq_ignore_ascii_case("iso"))
        .unwrap_or(false)
}

#[cfg(windows)]
fn mount_iso(path: &Path) -> Result<PreparedSource> {
    windows_impl::mount_iso(path)
}

#[cfg(not(windows))]
fn mount_iso(_path: &Path) -> Result<PreparedSource> {
    Err(anyhow!("ISO mounting requires Windows"))
}

fn is_wim(path: &Path) -> bool {
    path.extension()
        .and_then(|ext| ext.to_str())
        .map(|ext| {
            ext.eq_ignore_ascii_case("wim") || ext.eq_ignore_ascii_case("esd")
        })
        .unwrap_or(false)
}

#[cfg(windows)]
mod windows_impl {
    use super::{PreparedSource, SourceKind};
    use anyhow::{anyhow, Result};
    use std::collections::HashSet;
    use std::path::{Path, PathBuf};
    use std::time::{Duration, Instant};

    use windows::core::PCWSTR;
    use windows::Win32::Foundation::{CloseHandle, HANDLE, INVALID_HANDLE_VALUE};
    use windows::Win32::Storage::FileSystem::GetLogicalDrives;
    use windows::Win32::Storage::Vhd::{
        AttachVirtualDisk, DetachVirtualDisk, OpenVirtualDisk, ATTACH_VIRTUAL_DISK_FLAG_READ_ONLY,
        ATTACH_VIRTUAL_DISK_PARAMETERS, ATTACH_VIRTUAL_DISK_VERSION_1,
        DETACH_VIRTUAL_DISK_FLAG_NONE, OPEN_VIRTUAL_DISK_FLAG_NONE,
        OPEN_VIRTUAL_DISK_PARAMETERS, OPEN_VIRTUAL_DISK_VERSION_1, VIRTUAL_DISK_ACCESS_READ,
        VIRTUAL_STORAGE_TYPE, VIRTUAL_STORAGE_TYPE_DEVICE_ISO,
        VIRTUAL_STORAGE_TYPE_VENDOR_MICROSOFT,
    };

    pub fn mount_iso(path: &Path) -> Result<PreparedSource> {
        let before = logical_drive_letters();
        let handle = open_virtual_disk(path)?;
        attach_read_only(handle)?;
        let letter = wait_for_new_drive_letter(&before, Duration::from_secs(20))?;
        let root = PathBuf::from(format!("{}:\\", letter));
        Ok(PreparedSource {
            root,
            kind: SourceKind::Iso,
            _mount: Some(IsoMount { handle }),
        })
    }

    #[derive(Debug)]
    struct IsoMount {
        handle: HANDLE,
    }

    impl Drop for IsoMount {
        fn drop(&mut self) {
            unsafe {
                let _ = DetachVirtualDisk(self.handle, DETACH_VIRTUAL_DISK_FLAG_NONE, 0);
                let _ = CloseHandle(self.handle);
            }
        }
    }

    fn open_virtual_disk(path: &Path) -> Result<HANDLE> {
        let path_wide = wide(path);
        let storage_type = VIRTUAL_STORAGE_TYPE {
            DeviceId: VIRTUAL_STORAGE_TYPE_DEVICE_ISO,
            VendorId: VIRTUAL_STORAGE_TYPE_VENDOR_MICROSOFT,
        };

        let mut handle = HANDLE::default();
        let mut params = OPEN_VIRTUAL_DISK_PARAMETERS::default();
        params.Version = OPEN_VIRTUAL_DISK_VERSION_1;

        unsafe {
            OpenVirtualDisk(
                &storage_type,
                PCWSTR(path_wide.as_ptr()),
                VIRTUAL_DISK_ACCESS_READ,
                OPEN_VIRTUAL_DISK_FLAG_NONE,
                Some(&mut params),
                &mut handle,
            )
            .ok()
            .map_err(|error| anyhow!("OpenVirtualDisk failed: {:?}", error))?;

            if handle == INVALID_HANDLE_VALUE {
                return Err(anyhow!("OpenVirtualDisk returned invalid handle"));
            }
        }

        Ok(handle)
    }

    fn attach_read_only(handle: HANDLE) -> Result<()> {
        let mut params = ATTACH_VIRTUAL_DISK_PARAMETERS::default();
        params.Version = ATTACH_VIRTUAL_DISK_VERSION_1;

        unsafe {
            AttachVirtualDisk(
                handle,
                None,
                ATTACH_VIRTUAL_DISK_FLAG_READ_ONLY,
                0,
                Some(&mut params),
                None,
            )
            .ok()
            .map_err(|error| anyhow!("AttachVirtualDisk failed: {:?}", error))?;
        }

        Ok(())
    }

    fn logical_drive_letters() -> Vec<char> {
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
                return Err(anyhow!("timed out waiting for ISO mount"));
            }
            std::thread::sleep(Duration::from_millis(250));
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

#[cfg(not(windows))]
struct IsoMount;
