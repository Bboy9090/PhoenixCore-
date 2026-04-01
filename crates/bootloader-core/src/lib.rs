use anyhow::{anyhow, Result};
use std::path::{Path, PathBuf};

#[derive(Debug, Clone)]
pub struct BootloaderPackage {
    pub root: PathBuf,
    pub boot_entries: Vec<BootEntry>,
}

#[derive(Debug, Clone)]
pub struct BootEntry {
    pub path: String,
    pub arch: BootArch,
}

#[derive(Debug, Clone)]
pub enum BootArch {
    X64,
    Aarch64,
    Ia32,
    Unknown,
}

pub fn validate_bootloader_package(path: impl AsRef<Path>) -> Result<BootloaderPackage> {
    let root = path.as_ref().to_path_buf();
    if !root.is_dir() {
        return Err(anyhow!("bootloader root is not a directory"));
    }
    let mut entries = Vec::new();
    for (rel, arch) in [
        ("EFI/BOOT/BOOTX64.EFI", BootArch::X64),
        ("EFI/BOOT/BOOTAA64.EFI", BootArch::Aarch64),
        ("EFI/BOOT/BOOTIA32.EFI", BootArch::Ia32),
    ] {
        let candidate = root.join(rel);
        if candidate.exists() {
            entries.push(BootEntry {
                path: rel.to_string(),
                arch,
            });
        }
    }

    if entries.is_empty() {
        return Err(anyhow!("bootloader package missing EFI/BOOT/*.EFI entries"));
    }

    Ok(BootloaderPackage {
        root,
        boot_entries: entries,
    })
}
