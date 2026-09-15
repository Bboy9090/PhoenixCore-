use serde::Serialize;
use std::{
    fs::{self, File},
    io::{Read, Seek, SeekFrom},
    path::{Path, PathBuf},
};

#[derive(Debug, Clone, Serialize, PartialEq, Eq)]
pub struct WindowsBackupAnalysis {
    pub schema: &'static str,
    pub path: String,
    pub kind: String,
    pub size_bytes: Option<u64>,
    pub detected_by: Vec<String>,
    pub has_boot_wim: bool,
    pub has_install_wim: bool,
    pub has_install_esd: bool,
    pub has_split_wim: bool,
    pub has_winre: bool,
    pub has_efi: bool,
    pub has_bcd: bool,
    pub has_setup_exe: bool,
    pub restore_candidate: bool,
    pub destructive_actions_performed: bool,
    pub warnings: Vec<String>,
}

#[derive(Debug, Clone, Serialize, PartialEq, Eq)]
pub struct WindowsRecoveryPlan {
    pub schema: &'static str,
    pub source: WindowsBackupAnalysis,
    pub host_arch: String,
    pub host_os: String,
    pub traditional_bootcamp_supported: bool,
    pub allowed_operations: Vec<String>,
    pub blocked_operations: Vec<String>,
    pub required_gates: Vec<String>,
    pub dry_run: bool,
    pub destructive_actions_performed: bool,
}

fn contains_case_insensitive(haystack: &[u8], needle: &[u8]) -> bool {
    if needle.is_empty() || haystack.len() < needle.len() {
        return false;
    }
    haystack.windows(needle.len()).any(|window| {
        window
            .iter()
            .zip(needle)
            .all(|(left, right)| left.eq_ignore_ascii_case(right))
    })
}

fn read_prefix(path: &Path, max: usize) -> Result<Vec<u8>, String> {
    let mut file = File::open(path).map_err(|error| format!("cannot open backup source: {error}"))?;
    let mut buffer = vec![0; max];
    let count = file
        .read(&mut buffer)
        .map_err(|error| format!("cannot read backup source: {error}"))?;
    buffer.truncate(count);
    Ok(buffer)
}

fn read_tail(path: &Path, max: usize) -> Result<Vec<u8>, String> {
    let mut file = File::open(path).map_err(|error| format!("cannot open backup source: {error}"))?;
    let length = file
        .metadata()
        .map_err(|error| format!("cannot inspect backup source: {error}"))?
        .len();
    let read_len = usize::try_from(length.min(max as u64)).unwrap_or(max);
    file.seek(SeekFrom::End(-(read_len as i64)))
        .map_err(|error| format!("cannot seek backup source: {error}"))?;
    let mut buffer = vec![0; read_len];
    file.read_exact(&mut buffer)
        .map_err(|error| format!("cannot read backup source tail: {error}"))?;
    Ok(buffer)
}

fn directory_contains(root: &Path, candidates: &[&str]) -> bool {
    candidates.iter().any(|candidate| root.join(candidate).is_file())
}

fn detect_directory(path: &Path) -> WindowsBackupAnalysis {
    let has_boot_wim = directory_contains(path, &["sources/boot.wim", "Sources/boot.wim"]);
    let has_install_wim = directory_contains(path, &["sources/install.wim", "Sources/install.wim"]);
    let has_install_esd = directory_contains(path, &["sources/install.esd", "Sources/install.esd"]);
    let has_split_wim = fs::read_dir(path.join("sources"))
        .or_else(|_| fs::read_dir(path.join("Sources")))
        .ok()
        .map(|entries| {
            entries.filter_map(Result::ok).any(|entry| {
                entry
                    .path()
                    .extension()
                    .and_then(|value| value.to_str())
                    .is_some_and(|extension| extension.eq_ignore_ascii_case("swm"))
            })
        })
        .unwrap_or(false);
    let has_winre = directory_contains(
        path,
        &[
            "Windows/System32/Recovery/Winre.wim",
            "windows/system32/recovery/winre.wim",
            "Recovery/WindowsRE/Winre.wim",
        ],
    );
    let has_efi = path.join("EFI").is_dir()
        || path.join("efi").is_dir()
        || path.join("EFI/Microsoft/Boot").is_dir();
    let has_bcd = directory_contains(
        path,
        &[
            "EFI/Microsoft/Boot/BCD",
            "efi/microsoft/boot/BCD",
            "Boot/BCD",
            "boot/BCD",
        ],
    );
    let has_setup_exe = directory_contains(path, &["setup.exe", "Setup.exe"]);

    let windows_image_present = has_install_wim || has_install_esd || has_split_wim;
    let restore_candidate = windows_image_present || has_winre;
    let mut detected_by = Vec::new();
    if windows_image_present {
        detected_by.push("windows_installer_tree".to_string());
    }
    if has_winre {
        detected_by.push("winre_tree".to_string());
    }
    if has_efi {
        detected_by.push("efi_tree".to_string());
    }

    WindowsBackupAnalysis {
        schema: "phoenix_key.windows_backup_analysis.v1",
        path: path.to_string_lossy().to_string(),
        kind: if windows_image_present {
            "extracted_windows_media".to_string()
        } else if has_winre {
            "windows_recovery_tree".to_string()
        } else {
            "directory_unknown".to_string()
        },
        size_bytes: None,
        detected_by,
        has_boot_wim,
        has_install_wim,
        has_install_esd,
        has_split_wim,
        has_winre,
        has_efi,
        has_bcd,
        has_setup_exe,
        restore_candidate,
        destructive_actions_performed: false,
        warnings: if restore_candidate {
            Vec::new()
        } else {
            vec!["directory does not contain a recognized Windows restore payload".to_string()]
        },
    }
}

fn detect_file(path: &Path) -> Result<WindowsBackupAnalysis, String> {
    let metadata = path
        .metadata()
        .map_err(|error| format!("cannot inspect backup source: {error}"))?;
    let prefix = read_prefix(path, 0x9000)?;
    let tail = read_tail(path, 4096)?;

    let wim = prefix.starts_with(b"MSWIM\0\0\0");
    let vhdx = prefix.starts_with(b"vhdxfile");
    let vhd = contains_case_insensitive(&tail, b"conectix");
    let iso = prefix
        .get(0x8001..0x8006)
        .is_some_and(|signature| signature == b"CD001");

    let extension = path
        .extension()
        .and_then(|value| value.to_str())
        .unwrap_or("")
        .to_ascii_lowercase();

    let (kind, detected_by, restore_candidate) = if wim {
        (
            if extension == "esd" { "esd" } else { "wim" },
            vec!["MSWIM signature".to_string()],
            true,
        )
    } else if vhdx {
        ("vhdx", vec!["vhdxfile signature".to_string()], true)
    } else if vhd {
        ("vhd", vec!["conectix footer".to_string()], true)
    } else if iso {
        ("iso", vec!["ISO9660 CD001 descriptor".to_string()], true)
    } else if extension == "ffu" {
        (
            "ffu_unverified",
            vec!["filename extension only".to_string()],
            false,
        )
    } else if extension == "swm" {
        (
            "split_wim_unverified",
            vec!["filename extension only".to_string()],
            false,
        )
    } else {
        ("file_unknown", Vec::new(), false)
    };

    let warnings = match kind {
        "ffu_unverified" | "split_wim_unverified" => vec![
            "format was not accepted as restore-ready because only the filename extension matched"
                .to_string(),
        ],
        "file_unknown" => vec!["file signature is not recognized".to_string()],
        _ => Vec::new(),
    };

    Ok(WindowsBackupAnalysis {
        schema: "phoenix_key.windows_backup_analysis.v1",
        path: path.to_string_lossy().to_string(),
        kind: kind.to_string(),
        size_bytes: Some(metadata.len()),
        detected_by,
        has_boot_wim: false,
        has_install_wim: wim && extension == "wim",
        has_install_esd: wim && extension == "esd",
        has_split_wim: false,
        has_winre: false,
        has_efi: false,
        has_bcd: false,
        has_setup_exe: false,
        restore_candidate,
        destructive_actions_performed: false,
        warnings,
    })
}

pub fn analyze_backup_path(path: impl AsRef<Path>) -> Result<WindowsBackupAnalysis, String> {
    let path = path.as_ref();
    if !path.exists() {
        return Err("backup source does not exist".to_string());
    }
    if path.is_dir() {
        Ok(detect_directory(path))
    } else if path.is_file() {
        detect_file(path)
    } else {
        Err("backup source is neither a regular file nor a directory".to_string())
    }
}

pub fn build_recovery_plan(path: impl AsRef<Path>) -> Result<WindowsRecoveryPlan, String> {
    let source = analyze_backup_path(path)?;
    let host_arch = std::env::consts::ARCH.to_string();
    let host_os = std::env::consts::OS.to_string();
    let apple_silicon = host_os == "macos" && matches!(host_arch.as_str(), "aarch64" | "arm64");
    let traditional_bootcamp_supported = host_os == "macos" && !apple_silicon && host_arch == "x86_64";

    let mut allowed_operations = vec![
        "inspect_backup".to_string(),
        "generate_recovery_report".to_string(),
        "verify_source_integrity".to_string(),
    ];
    let mut blocked_operations = Vec::new();

    if source.restore_candidate {
        allowed_operations.push("plan_recovery_media".to_string());
    } else {
        blocked_operations.push("restore_source_not_verified".to_string());
    }

    if traditional_bootcamp_supported {
        allowed_operations.push("plan_bootcamp_repair".to_string());
        allowed_operations.push("plan_bootcamp_restore".to_string());
    } else {
        blocked_operations.push("traditional_bootcamp_restore".to_string());
    }

    if apple_silicon {
        allowed_operations.push("plan_windows_arm_recovery_media".to_string());
        allowed_operations.push("plan_vhdx_vm_recovery".to_string());
    }

    Ok(WindowsRecoveryPlan {
        schema: "phoenix_key.windows_recovery_plan.v1",
        source,
        host_arch,
        host_os,
        traditional_bootcamp_supported,
        allowed_operations,
        blocked_operations,
        required_gates: vec![
            "source_integrity".to_string(),
            "fresh_device_enumeration".to_string(),
            "target_identity".to_string(),
            "free_space".to_string(),
            "partition_manifest".to_string(),
            "explicit_destructive_authorization".to_string(),
            "fresh_prewrite_identity_recheck".to_string(),
        ],
        dry_run: true,
        destructive_actions_performed: false,
    })
}

pub fn fixture_candidates(root: impl AsRef<Path>) -> Result<Vec<PathBuf>, String> {
    let root = root.as_ref();
    if !root.is_dir() {
        return Err("fixture root is not a directory".to_string());
    }
    let mut candidates = Vec::new();
    for entry in fs::read_dir(root).map_err(|error| format!("cannot read fixture root: {error}"))? {
        let entry = entry.map_err(|error| format!("cannot read fixture entry: {error}"))?;
        let path = entry.path();
        if path.is_dir() {
            let analysis = detect_directory(&path);
            if analysis.restore_candidate || analysis.has_efi || analysis.has_bcd {
                candidates.push(path);
            }
        } else if path.is_file() {
            let extension = path
                .extension()
                .and_then(|value| value.to_str())
                .unwrap_or("")
                .to_ascii_lowercase();
            if matches!(extension.as_str(), "iso" | "wim" | "esd" | "swm" | "vhd" | "vhdx" | "ffu") {
                candidates.push(path);
            }
        }
    }
    candidates.sort();
    Ok(candidates)
}

#[cfg(test)]
mod tests {
    use super::{analyze_backup_path, build_recovery_plan};
    use std::{fs, io::Write};

    fn temp_case(name: &str) -> std::path::PathBuf {
        let path = std::env::temp_dir().join(format!(
            "phoenix-key-windows-recovery-{name}-{}",
            std::process::id()
        ));
        let _ = fs::remove_dir_all(&path);
        fs::create_dir_all(&path).unwrap();
        path
    }

    #[test]
    fn detects_wim_by_signature_not_extension() {
        let root = temp_case("wim");
        let path = root.join("backup.bin");
        fs::write(&path, b"MSWIM\0\0\0fixture").unwrap();
        let analysis = analyze_backup_path(&path).unwrap();
        assert_eq!(analysis.kind, "wim");
        assert!(analysis.restore_candidate);
        assert_eq!(analysis.detected_by, vec!["MSWIM signature"]);
        assert!(!analysis.destructive_actions_performed);
        fs::remove_dir_all(root).unwrap();
    }

    #[test]
    fn rejects_extension_only_ffu_as_restore_ready() {
        let root = temp_case("ffu");
        let path = root.join("backup.ffu");
        fs::write(&path, b"not-an-ffu").unwrap();
        let analysis = analyze_backup_path(&path).unwrap();
        assert_eq!(analysis.kind, "ffu_unverified");
        assert!(!analysis.restore_candidate);
        fs::remove_dir_all(root).unwrap();
    }

    #[test]
    fn detects_extracted_windows_tree() {
        let root = temp_case("tree");
        fs::create_dir_all(root.join("sources")).unwrap();
        fs::create_dir_all(root.join("EFI/Microsoft/Boot")).unwrap();
        fs::write(root.join("sources/install.wim"), b"fixture").unwrap();
        fs::write(root.join("sources/boot.wim"), b"fixture").unwrap();
        fs::write(root.join("setup.exe"), b"fixture").unwrap();
        fs::write(root.join("EFI/Microsoft/Boot/BCD"), b"fixture").unwrap();

        let analysis = analyze_backup_path(&root).unwrap();
        assert_eq!(analysis.kind, "extracted_windows_media");
        assert!(analysis.has_install_wim);
        assert!(analysis.has_boot_wim);
        assert!(analysis.has_setup_exe);
        assert!(analysis.has_efi);
        assert!(analysis.has_bcd);
        assert!(analysis.restore_candidate);
        fs::remove_dir_all(root).unwrap();
    }

    #[test]
    fn recovery_plan_is_always_dry_run_and_non_destructive() {
        let root = temp_case("plan");
        let path = root.join("fixture.wim");
        let mut file = fs::File::create(&path).unwrap();
        file.write_all(b"MSWIM\0\0\0fixture").unwrap();
        let plan = build_recovery_plan(&path).unwrap();
        assert!(plan.dry_run);
        assert!(!plan.destructive_actions_performed);
        assert!(plan.required_gates.contains(&"fresh_prewrite_identity_recheck".to_string()));
        fs::remove_dir_all(root).unwrap();
    }
}
