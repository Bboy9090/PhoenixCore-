use anyhow::{anyhow, Context, Result};
use phoenix_report::{
    create_report_bundle_with_meta_and_signing, create_report_bundle_with_meta_signing_and_artifacts,
    ReportArtifact, ReportPaths,
};
use phoenix_safety::{can_write_to_disk, SafetyContext, SafetyDecision};
use phoenix_content::{prepare_source, resolve_windows_image, SourceKind};
use phoenix_host_windows::format::{format_existing_volume, prepare_usb_disk, FileSystem};
use phoenix_host_windows::space::free_space_bytes;
use phoenix_imaging::{
    hash_device_readonly, hash_disk_readonly_physicaldrive, make_chunk_plan,
    write_image_to_device,
};
use phoenix_wim::{apply_image as wim_apply_image, list_images as wim_list_images};
use phoenix_core::{DeviceGraph, WorkflowDefinition, WORKFLOW_SCHEMA_VERSION};
use phoenix_fs_fat32::format_fat32;
use phoenix_bootloader_core::validate_bootloader_package;
use sha2::{Digest, Sha256};
use std::time::Instant;
use std::fs;
use std::path::{Path, PathBuf};

pub trait Workflow {
    fn name(&self) -> &'static str;
    fn run(&self) -> Result<()>;
}

pub fn run_workflow<W: Workflow>(workflow: W) -> Result<()> {
    workflow.run()
}

#[derive(Debug, Clone)]
pub struct WindowsInstallerUsbParams {
    pub target_disk_id: String,
    pub source_path: PathBuf,
    pub target_mount: Option<PathBuf>,
    pub report_base: PathBuf,
    pub force: bool,
    pub confirmation_token: Option<String>,
    pub dry_run: bool,
    pub repartition: bool,
    pub format: bool,
    pub filesystem: FileSystem,
    pub label: Option<String>,
    pub driver_source: Option<PathBuf>,
    pub driver_target: Option<PathBuf>,
    pub hash_manifest: bool,
}

#[derive(Debug, Clone)]
pub struct WindowsInstallerUsbResult {
    pub report: ReportPaths,
    pub target_mount: PathBuf,
    pub copied_files: usize,
    pub copied_bytes: u64,
    pub driver_files: usize,
    pub driver_bytes: u64,
    pub dry_run: bool,
}

#[derive(Debug, Clone)]
pub struct UnixInstallerUsbParams {
    pub source_path: PathBuf,
    pub target_mount: PathBuf,
    pub report_base: PathBuf,
    pub force: bool,
    pub confirmation_token: Option<String>,
    pub dry_run: bool,
    pub hash_manifest: bool,
    pub format_device: Option<PathBuf>,
    pub format_size_bytes: Option<u64>,
    pub format_label: Option<String>,
}

#[derive(Debug, Clone)]
pub struct UnixWriteImageParams {
    pub source_image: PathBuf,
    pub target_device: PathBuf,
    pub report_base: PathBuf,
    pub force: bool,
    pub confirmation_token: Option<String>,
    pub dry_run: bool,
    pub verify: bool,
    pub chunk_size: u64,
}

#[derive(Debug, Clone)]
pub struct UnixWriteImageResult {
    pub report: ReportPaths,
    pub bytes_written: u64,
    pub sha256: String,
    pub verify_ok: Option<bool>,
    pub dry_run: bool,
}

#[derive(Debug, Clone)]
pub struct MacosInstallerUsbParams {
    pub source_path: PathBuf,
    pub target_device: PathBuf,
    pub report_base: PathBuf,
    pub volume_name: String,
    pub macos_version: Option<String>,
    pub filesystem: Option<String>,
    pub force: bool,
    pub confirmation_token: Option<String>,
    pub dry_run: bool,
}

#[derive(Debug, Clone)]
pub struct MacosInstallerUsbResult {
    pub report: ReportPaths,
    pub mode: String,
    pub target_volume: PathBuf,
    pub dry_run: bool,
}

#[derive(Debug, Clone)]
pub struct UnixBootPrepParams {
    pub source_path: PathBuf,
    pub target_mount: PathBuf,
    pub report_base: PathBuf,
    pub force: bool,
    pub confirmation_token: Option<String>,
    pub dry_run: bool,
    pub hash_manifest: bool,
}

#[derive(Debug, Clone)]
pub struct UnixBootPrepResult {
    pub report: ReportPaths,
    pub copied_files: usize,
    pub copied_bytes: u64,
    pub dry_run: bool,
}

#[derive(Debug, Clone)]
pub struct BootloaderStageParams {
    pub source_path: PathBuf,
    pub target_mount: PathBuf,
    pub target_subdir: Option<PathBuf>,
    pub report_base: PathBuf,
    pub force: bool,
    pub confirmation_token: Option<String>,
    pub dry_run: bool,
    pub hash_manifest: bool,
}

#[derive(Debug, Clone)]
pub struct BootloaderStageResult {
    pub report: ReportPaths,
    pub copied_files: usize,
    pub copied_bytes: u64,
    pub dry_run: bool,
}

#[derive(Debug, Clone)]
pub struct UnixInstallerUsbResult {
    pub report: ReportPaths,
    pub target_mount: PathBuf,
    pub copied_files: usize,
    pub copied_bytes: u64,
    pub dry_run: bool,
}

pub struct WindowsInstallerUsbWorkflow {
    params: WindowsInstallerUsbParams,
}

impl WindowsInstallerUsbWorkflow {
    pub fn new(params: WindowsInstallerUsbParams) -> Self {
        Self { params }
    }

    pub fn execute(&self) -> Result<WindowsInstallerUsbResult> {
        run_windows_installer_usb(&self.params)
    }
}

impl Workflow for WindowsInstallerUsbWorkflow {
    fn name(&self) -> &'static str {
        "windows-installer-usb"
    }

    fn run(&self) -> Result<()> {
        self.execute().map(|_| ())
    }
}

pub fn run_windows_installer_usb(params: &WindowsInstallerUsbParams) -> Result<WindowsInstallerUsbResult> {
    let graph = build_device_graph()?;
    let disk = graph
        .disks
        .iter()
        .find(|disk| disk.id.eq_ignore_ascii_case(&params.target_disk_id))
        .ok_or_else(|| anyhow!("disk not found: {}", params.target_disk_id))?;

    if disk.is_system_disk {
        return Err(anyhow!("refusing to target system disk: {}", disk.id));
    }

    if !disk.removable {
        return Err(anyhow!(
            "target disk is not marked removable: {}",
            disk.id
        ));
    }

    let mut target_mount = if let Some(path) = &params.target_mount {
        let normalized = normalize_mount_path(path);
        let normalized_str = normalized.display().to_string();
        let belongs = disk.partitions.iter().any(|partition| {
            partition
                .mount_points
                .iter()
                .any(|mount| mount.eq_ignore_ascii_case(&normalized_str))
        });
        if !belongs {
            return Err(anyhow!(
                "target_mount {} does not belong to disk {}",
                normalized.display(),
                disk.id
            ));
        }
        normalized
    } else {
        disk.partitions
            .iter()
            .flat_map(|partition| partition.mount_points.iter())
            .next()
            .map(|mount| normalize_mount_path(&PathBuf::from(mount)))
            .unwrap_or_else(|| PathBuf::new())
    };

    let mut fs_label = None;
    let target_mount_string = target_mount.display().to_string();
    for partition in &disk.partitions {
        if partition
            .mount_points
            .iter()
            .any(|mount| mount.eq_ignore_ascii_case(&target_mount_string))
        {
            fs_label = partition.fs.clone();
            break;
        }
    }

    if let Some(fs) = fs_label.as_deref() {
        let fs_upper = fs.to_ascii_uppercase();
        if fs_upper != "FAT32" && fs_upper != "NTFS" && fs_upper != "EXFAT" {
            return Err(anyhow!("unsupported filesystem for staging: {}", fs));
        }
    }

    let prepared = prepare_source(&params.source_path)?;
    let source_root = prepared.root.clone();
    let source_kind = prepared.kind;
    if !source_root.is_dir() {
        return Err(anyhow!("source root is not a directory"));
    }

    let setup_exe = source_root.join("setup.exe");
    if !setup_exe.exists() {
        return Err(anyhow!(
            "source missing setup.exe (provide extracted Windows installer files)"
        ));
    }

    let files = collect_files(&source_root)?;
    ensure_boot_files(&files)?;
    let total_bytes = files.iter().map(|entry| entry.size).sum::<u64>();

    let mut logs = Vec::new();
    logs.push(format!("workflow=windows-installer-usb"));
    logs.push(format!("target_disk={}", disk.id));
    logs.push(format!("target_mount={}", target_mount.display()));
    logs.push(format!("source_path={}", source_root.display()));
    logs.push(format!("source_kind={:?}", source_kind));
    logs.push(format!("file_count={}", files.len()));
    logs.push(format!("total_bytes={}", total_bytes));
    logs.push(format!("filesystem={}", params.filesystem.as_str()));

    let mut copied_files = 0usize;
    let mut copied_bytes = 0u64;
    let mut driver_files = 0usize;
    let mut driver_bytes = 0u64;
    let mut copy_manifest = Vec::new();
    let mut driver_manifest = Vec::new();
    let mut artifacts = Vec::new();
    let mut artifact_names = Vec::new();

    if params.filesystem.as_str().eq_ignore_ascii_case("FAT32") {
        let max = max_file_size(&files);
        if max > FAT32_MAX_FILE {
            return Err(anyhow!(
                "FAT32 cannot store files > 4GB (max file {} bytes). Use NTFS/exFAT.",
                max
            ));
        }
    }

    if !params.dry_run {
        let ctx = SafetyContext {
            force_mode: params.force,
            confirmation_token: params.confirmation_token.clone(),
        };

        match can_write_to_disk(&ctx, disk.is_system_disk) {
            SafetyDecision::Allow => {}
            SafetyDecision::Deny(reason) => return Err(anyhow!(reason)),
        }

        if params.repartition {
            let disk_number = parse_disk_number(&disk.id)
                .ok_or_else(|| anyhow!("invalid disk id {}", disk.id))?;
            let letter = prepare_usb_disk(
                disk_number,
                disk.size_bytes,
                params.filesystem,
                params.label.as_deref(),
            )?;
            target_mount = normalize_mount_path(&PathBuf::from(format!("{}:\\", letter)));
            logs.push("partition_format=completed".to_string());
        } else if params.format {
            let letter = extract_drive_letter(&target_mount)
                .ok_or_else(|| anyhow!("unable to parse drive letter from mount path"))?;
            format_existing_volume(letter, params.filesystem, params.label.as_deref())?;
            logs.push("partition_format=formatted".to_string());
        } else {
            logs.push("partition_format=skipped".to_string());
        }

        if target_mount.as_os_str().is_empty() {
            return Err(anyhow!("no mounted volume found for {}", disk.id));
        }

        if let Ok(free_bytes) = free_space_bytes(&target_mount.display().to_string()) {
            if free_bytes < total_bytes {
                return Err(anyhow!(
                    "insufficient free space: required {}, available {}",
                    total_bytes,
                    free_bytes
                ));
            }
        }

        logs.push("copy_start".to_string());
        for entry in &files {
            let dest_path = target_mount.join(&entry.relative_path);
            if let Some(parent) = dest_path.parent() {
                fs::create_dir_all(parent)
                    .with_context(|| format!("create dir {}", parent.display()))?;
            }
            fs::copy(&entry.absolute_path, &dest_path).with_context(|| {
                format!(
                    "copy {} to {}",
                    entry.absolute_path.display(),
                    dest_path.display()
                )
            })?;
            copied_files += 1;
            copied_bytes = copied_bytes.saturating_add(entry.size);
            if params.hash_manifest {
                let hash = hash_file(&entry.absolute_path)?;
                copy_manifest.push(CopyManifestEntry {
                    path: entry.relative_path.to_string_lossy().to_string(),
                    bytes: entry.size,
                    sha256: hash,
                });
            }
        }
        logs.push("copy_complete".to_string());

        verify_copy(&target_mount, &files)?;
        logs.push("verify_complete".to_string());

        if let Some(driver_source) = &params.driver_source {
            let driver_source = fs::canonicalize(driver_source)
                .unwrap_or_else(|_| driver_source.clone());
            if !driver_source.is_dir() {
                return Err(anyhow!("driver_source is not a directory"));
            }
            let driver_target = params
                .driver_target
                .clone()
                .unwrap_or_else(default_driver_target);
            let driver_target = target_mount.join(driver_target);
            let driver_entries = collect_files(&driver_source)?;

            logs.push(format!("driver_source={}", driver_source.display()));
            logs.push(format!("driver_target={}", driver_target.display()));
            logs.push(format!("driver_file_count={}", driver_entries.len()));

            for entry in &driver_entries {
                let dest_path = driver_target.join(&entry.relative_path);
                if let Some(parent) = dest_path.parent() {
                    fs::create_dir_all(parent).with_context(|| {
                        format!("create dir {}", parent.display())
                    })?;
                }
                fs::copy(&entry.absolute_path, &dest_path).with_context(|| {
                    format!(
                        "copy driver {} to {}",
                        entry.absolute_path.display(),
                        dest_path.display()
                    )
                })?;
                driver_files += 1;
                driver_bytes = driver_bytes.saturating_add(entry.size);
                if params.hash_manifest {
                    let hash = hash_file(&entry.absolute_path)?;
                    driver_manifest.push(CopyManifestEntry {
                        path: entry.relative_path.to_string_lossy().to_string(),
                        bytes: entry.size,
                        sha256: hash,
                    });
                }
            }
            logs.push("driver_copy_complete".to_string());
        }

        if params.hash_manifest {
            if !copy_manifest.is_empty() {
                let bytes = serde_json::to_vec_pretty(&copy_manifest)?;
                artifacts.push(ReportArtifact {
                    name: "copy_manifest.json".to_string(),
                    bytes,
                });
                artifact_names.push("copy_manifest.json".to_string());
            }
            if !driver_manifest.is_empty() {
                let bytes = serde_json::to_vec_pretty(&driver_manifest)?;
                artifacts.push(ReportArtifact {
                    name: "driver_manifest.json".to_string(),
                    bytes,
                });
                artifact_names.push("driver_manifest.json".to_string());
            }
        }
    } else {
        logs.push("dry_run=true".to_string());
    }

    let meta = serde_json::json!({
        "workflow": "windows-installer-usb",
        "status": if params.dry_run { "dry_run" } else { "completed" },
        "target_disk_id": disk.id,
        "target_mount": target_mount.display().to_string(),
        "source_path": source_root.display().to_string(),
        "source_kind": format!("{:?}", source_kind),
        "copied_files": copied_files,
        "copied_bytes": copied_bytes,
        "driver_files": driver_files,
        "driver_bytes": driver_bytes,
        "artifacts": artifact_names,
        "dry_run": params.dry_run
    });

    let report = create_report_bundle_with_meta_signing_and_artifacts(
        &params.report_base,
        &graph,
        Some(meta),
        Some(&logs.join("\n")),
        signing_key_from_env().as_deref(),
        &artifacts,
    )?;

    Ok(WindowsInstallerUsbResult {
        report,
        target_mount,
        copied_files,
        copied_bytes,
        driver_files,
        driver_bytes,
        dry_run: params.dry_run,
    })
}

pub fn run_unix_installer_usb(params: &UnixInstallerUsbParams) -> Result<UnixInstallerUsbResult> {
    #[cfg(not(any(target_os = "linux", target_os = "macos")))]
    {
        return Err(anyhow!("unix installer workflow requires linux or macos"));
    }

    let graph = build_device_graph()?;
    let target_mount = normalize_mount_for_unix(&params.target_mount);
    if !target_mount.exists() {
        return Err(anyhow!("target mount does not exist"));
    }
    if !target_mount.is_dir() {
        return Err(anyhow!("target mount is not a directory"));
    }
    let disk = find_disk_by_mount(&graph, &target_mount)
        .ok_or_else(|| anyhow!("target mount not found in device graph"))?;

    if disk.is_system_disk {
        return Err(anyhow!("refusing to target system disk: {}", disk.id));
    }
    if !disk.removable {
        return Err(anyhow!(
            "target disk is not marked removable: {}",
            disk.id
        ));
    }

    let prepared = prepare_source(&params.source_path)?;
    let source_root = prepared.root.clone();
    if !source_root.is_dir() {
        return Err(anyhow!("source root is not a directory"));
    }

    let files = collect_files(&source_root)?;
    let total_bytes = files.iter().map(|entry| entry.size).sum::<u64>();

    ensure_unix_boot_files(&files, current_os())?;

    if let Some(free_bytes) = free_space_bytes(&target_mount)? {
        if free_bytes < total_bytes {
            return Err(anyhow!(
                "insufficient free space: required {}, available {}",
                total_bytes,
                free_bytes
            ));
        }
    }

    let mut logs = Vec::new();
    logs.push("workflow=unix-installer-usb".to_string());
    logs.push(format!("target_disk={}", disk.id));
    logs.push(format!("target_mount={}", target_mount.display()));
    logs.push(format!("source_path={}", source_root.display()));
    logs.push(format!("file_count={}", files.len()));
    logs.push(format!("total_bytes={}", total_bytes));

    let mut copied_files = 0usize;
    let mut copied_bytes = 0u64;
    let mut artifacts = Vec::new();
    let mut artifact_names = Vec::new();

    if !params.dry_run {
        let ctx = SafetyContext {
            force_mode: params.force,
            confirmation_token: params.confirmation_token.clone(),
        };
        match can_write_to_disk(&ctx, disk.is_system_disk) {
            SafetyDecision::Allow => {}
            SafetyDecision::Deny(reason) => return Err(anyhow!(reason)),
        }

        if let Some(device_path) = &params.format_device {
            let size_bytes = params
                .format_size_bytes
                .ok_or_else(|| anyhow!("format_size_bytes required when format_device set"))?;
            format_fat32(device_path, size_bytes, params.format_label.as_deref())?;
            logs.push(format!("format_fat32={}", device_path.display()));
        }

        let test_path = target_mount.join(".phoenix_write_test");
        fs::write(&test_path, b"")?;
        fs::remove_file(&test_path).ok();
        logs.push("write_test=ok".to_string());

        logs.push("copy_start".to_string());
        let mut copy_manifest = Vec::new();
        for entry in &files {
            let dest_path = target_mount.join(&entry.relative_path);
            if let Some(parent) = dest_path.parent() {
                fs::create_dir_all(parent)
                    .with_context(|| format!("create dir {}", parent.display()))?;
            }
            fs::copy(&entry.absolute_path, &dest_path).with_context(|| {
                format!(
                    "copy {} to {}",
                    entry.absolute_path.display(),
                    dest_path.display()
                )
            })?;
            copied_files += 1;
            copied_bytes = copied_bytes.saturating_add(entry.size);
            if params.hash_manifest {
                let hash = hash_file(&entry.absolute_path)?;
                copy_manifest.push(CopyManifestEntry {
                    path: entry.relative_path.to_string_lossy().to_string(),
                    bytes: entry.size,
                    sha256: hash,
                });
            }
        }
        logs.push("copy_complete".to_string());
        verify_copy(&target_mount, &files)?;
        logs.push("verify_complete".to_string());

        if params.hash_manifest && !copy_manifest.is_empty() {
            let bytes = serde_json::to_vec_pretty(&copy_manifest)?;
            artifacts.push(ReportArtifact {
                name: "copy_manifest.json".to_string(),
                bytes,
            });
            artifact_names.push("copy_manifest.json".to_string());
        }
    } else {
        logs.push("dry_run=true".to_string());
    }

    let meta = serde_json::json!({
        "workflow": "unix-installer-usb",
        "status": if params.dry_run { "dry_run" } else { "completed" },
        "target_disk_id": disk.id,
        "target_mount": target_mount.display().to_string(),
        "source_path": source_root.display().to_string(),
        "copied_files": copied_files,
        "copied_bytes": copied_bytes,
        "artifacts": artifact_names,
        "dry_run": params.dry_run
    });

    let report = create_report_bundle_with_meta_signing_and_artifacts(
        &params.report_base,
        &graph,
        Some(meta),
        Some(&logs.join("\n")),
        signing_key_from_env().as_deref(),
        &artifacts,
    )?;

    Ok(UnixInstallerUsbResult {
        report,
        target_mount,
        copied_files,
        copied_bytes,
        dry_run: params.dry_run,
    })
}

pub fn run_unix_write_image(params: &UnixWriteImageParams) -> Result<UnixWriteImageResult> {
    #[cfg(not(any(target_os = "linux", target_os = "macos")))]
    {
        return Err(anyhow!("unix image writer requires linux or macos"));
    }

    let graph = build_device_graph()?;
    let disk_id = disk_id_from_device_path(&params.target_device)
        .ok_or_else(|| anyhow!("unsupported device path"))?;
    let disk = graph
        .disks
        .iter()
        .find(|disk| disk.id.eq_ignore_ascii_case(&disk_id))
        .ok_or_else(|| anyhow!("disk not found: {}", disk_id))?;

    if disk.is_system_disk {
        return Err(anyhow!("refusing to target system disk: {}", disk.id));
    }
    if !disk.removable {
        return Err(anyhow!(
            "target disk is not marked removable: {}",
            disk.id
        ));
    }

    let mut logs = Vec::new();
    logs.push("workflow=unix-write-image".to_string());
    logs.push(format!("target_device={}", params.target_device.display()));
    logs.push(format!("source_image={}", params.source_image.display()));
    logs.push(format!("verify={}", params.verify));
    logs.push(format!("dry_run={}", params.dry_run));

    let mut bytes_written = 0u64;
    let mut sha256 = String::new();
    let mut verify_ok = None;

    if !params.dry_run {
        let ctx = SafetyContext {
            force_mode: params.force,
            confirmation_token: params.confirmation_token.clone(),
        };
        match can_write_to_disk(&ctx, disk.is_system_disk) {
            SafetyDecision::Allow => {}
            SafetyDecision::Deny(reason) => return Err(anyhow!(reason)),
        }

        let result = write_image_to_device(
            &params.source_image,
            &params.target_device,
            params.chunk_size,
            params.verify,
        )?;
        bytes_written = result.bytes_written;
        sha256 = result.sha256;
        verify_ok = result.verify_ok;
        logs.push(format!("bytes_written={}", bytes_written));
        logs.push(format!("sha256={}", sha256));
        if let Some(ok) = verify_ok {
            logs.push(format!("verify_ok={}", ok));
        }
    }

    let meta = serde_json::json!({
        "workflow": "unix-write-image",
        "target_device": params.target_device.display().to_string(),
        "source_image": params.source_image.display().to_string(),
        "bytes_written": bytes_written,
        "sha256": sha256,
        "verify": params.verify,
        "verify_ok": verify_ok,
        "dry_run": params.dry_run
    });

    let report = create_report_bundle_with_meta_and_signing(
        &params.report_base,
        &graph,
        Some(meta),
        Some(&logs.join("\n")),
        signing_key_from_env().as_deref(),
    )?;

    Ok(UnixWriteImageResult {
        report,
        bytes_written,
        sha256,
        verify_ok,
        dry_run: params.dry_run,
    })
}

pub fn run_macos_installer_usb(params: &MacosInstallerUsbParams) -> Result<MacosInstallerUsbResult> {
    #[cfg(not(target_os = "macos"))]
    {
        return Err(anyhow!("macos installer workflow requires macOS"));
    }

    let graph = build_device_graph()?;
    let disk_id = disk_id_from_device_path(&params.target_device)
        .ok_or_else(|| anyhow!("unsupported target device"))?;
    let disk = graph
        .disks
        .iter()
        .find(|disk| disk.id.eq_ignore_ascii_case(&disk_id))
        .ok_or_else(|| anyhow!("disk not found: {}", disk_id))?;

    if disk.is_system_disk {
        return Err(anyhow!("refusing to target system disk: {}", disk.id));
    }
    if !disk.removable {
        return Err(anyhow!(
            "target disk is not marked removable: {}",
            disk.id
        ));
    }

    let fs = params
        .filesystem
        .clone()
        .or_else(|| params.macos_version.as_deref().and_then(select_macos_fs))
        .unwrap_or_else(|| "APFS".to_string());

    let mut logs = Vec::new();
    logs.push("workflow=macos-installer-usb".to_string());
    logs.push(format!("target_device={}", params.target_device.display()));
    logs.push(format!("volume_name={}", params.volume_name));
    logs.push(format!("filesystem={}", fs));
    logs.push(format!("dry_run={}", params.dry_run));

    let mut mode = "unknown".to_string();
    let mut target_volume = PathBuf::from(format!("/Volumes/{}", params.volume_name));

    if !params.dry_run {
        let ctx = SafetyContext {
            force_mode: params.force,
            confirmation_token: params.confirmation_token.clone(),
        };
        match can_write_to_disk(&ctx, disk.is_system_disk) {
            SafetyDecision::Allow => {}
            SafetyDecision::Deny(reason) => return Err(anyhow!(reason)),
        }

        let source_path = params.source_path.clone();
        if source_path.extension().and_then(|e| e.to_str()).map(|e| e.eq_ignore_ascii_case("dmg")).unwrap_or(false) {
            let mounted = mount_dmg(&source_path)?;
            if let Some(app) = find_install_app(&mounted.mount_point) {
                mode = "createinstallmedia".to_string();
                logs.push(format!("installer_app={}", app.display()));
                erase_disk(&params.target_device, &fs, &params.volume_name)?;
                target_volume = PathBuf::from(format!("/Volumes/{}", params.volume_name));
                run_createinstallmedia(&app, &target_volume)?;
            } else {
                mode = "asr_restore".to_string();
                run_asr_restore(&source_path, &params.target_device)?;
            }
            drop(mounted);
        } else if is_macos_app(&source_path) {
            mode = "createinstallmedia".to_string();
            erase_disk(&params.target_device, &fs, &params.volume_name)?;
            target_volume = PathBuf::from(format!("/Volumes/{}", params.volume_name));
            run_createinstallmedia(&source_path, &target_volume)?;
        } else {
            return Err(anyhow!("unsupported macos source path"));
        }
    }

    let meta = serde_json::json!({
        "workflow": "macos-installer-usb",
        "status": if params.dry_run { "dry_run" } else { "completed" },
        "target_device": params.target_device.display().to_string(),
        "volume_name": params.volume_name,
        "filesystem": fs,
        "mode": mode,
        "dry_run": params.dry_run
    });

    let report = create_report_bundle_with_meta_and_signing(
        &params.report_base,
        &graph,
        Some(meta),
        Some(&logs.join("\n")),
        signing_key_from_env().as_deref(),
    )?;

    Ok(MacosInstallerUsbResult {
        report,
        mode,
        target_volume,
        dry_run: params.dry_run,
    })
}

pub fn run_stage_bootloader(params: &BootloaderStageParams) -> Result<BootloaderStageResult> {
    let graph = build_device_graph()?;
    let target_mount = normalize_mount_for_unix(&params.target_mount);
    if !target_mount.exists() || !target_mount.is_dir() {
        return Err(anyhow!("target mount is invalid"));
    }

    let disk = find_disk_by_mount(&graph, &target_mount)
        .ok_or_else(|| anyhow!("target mount not found in device graph"))?;
    if disk.is_system_disk {
        return Err(anyhow!("refusing to target system disk: {}", disk.id));
    }
    if !disk.removable {
        return Err(anyhow!(
            "target disk is not marked removable: {}",
            disk.id
        ));
    }

    let package = validate_bootloader_package(&params.source_path)?;
    let staging_root = if let Some(subdir) = &params.target_subdir {
        target_mount.join(subdir)
    } else {
        target_mount.clone()
    };

    let mut logs = Vec::new();
    logs.push("workflow=stage-bootloader".to_string());
    logs.push(format!("target_mount={}", target_mount.display()));
    logs.push(format!("source_path={}", package.root.display()));
    logs.push(format!("entries={}", package.boot_entries.len()));

    let mut copied_files = 0usize;
    let mut copied_bytes = 0u64;
    let mut artifacts = Vec::new();
    let mut artifact_names = Vec::new();

    if !params.dry_run {
        let ctx = SafetyContext {
            force_mode: params.force,
            confirmation_token: params.confirmation_token.clone(),
        };
        match can_write_to_disk(&ctx, disk.is_system_disk) {
            SafetyDecision::Allow => {}
            SafetyDecision::Deny(reason) => return Err(anyhow!(reason)),
        }

        let test_path = target_mount.join(".phoenix_write_test");
        fs::write(&test_path, b"")?;
        fs::remove_file(&test_path).ok();

        let stats = copy_dir_recursive(&package.root, &staging_root, params.hash_manifest)?;
        copied_files = stats.files;
        copied_bytes = stats.bytes;
        if params.hash_manifest && !stats.manifest.is_empty() {
            let bytes = serde_json::to_vec_pretty(&stats.manifest)?;
            artifacts.push(ReportArtifact {
                name: "bootloader_manifest.json".to_string(),
                bytes,
            });
            artifact_names.push("bootloader_manifest.json".to_string());
        }
        logs.push(format!("staged_to={}", staging_root.display()));
    } else {
        logs.push("dry_run=true".to_string());
    }

    let meta = serde_json::json!({
        "workflow": "stage-bootloader",
        "status": if params.dry_run { "dry_run" } else { "completed" },
        "target_mount": target_mount.display().to_string(),
        "staging_root": staging_root.display().to_string(),
        "copied_files": copied_files,
        "copied_bytes": copied_bytes,
        "artifacts": artifact_names,
        "dry_run": params.dry_run
    });

    let report = create_report_bundle_with_meta_signing_and_artifacts(
        &params.report_base,
        &graph,
        Some(meta),
        Some(&logs.join("\n")),
        signing_key_from_env().as_deref(),
        &artifacts,
    )?;

    Ok(BootloaderStageResult {
        report,
        copied_files,
        copied_bytes,
        dry_run: params.dry_run,
    })
}

pub fn run_unix_boot_prep(params: &UnixBootPrepParams) -> Result<UnixBootPrepResult> {
    #[cfg(not(any(target_os = "linux", target_os = "macos")))]
    {
        return Err(anyhow!("unix boot prep requires linux or macos"));
    }

    let graph = build_device_graph()?;
    let target_mount = normalize_mount_for_unix(&params.target_mount);
    if !target_mount.exists() || !target_mount.is_dir() {
        return Err(anyhow!("target mount is invalid"));
    }

    let disk = find_disk_by_mount(&graph, &target_mount)
        .ok_or_else(|| anyhow!("target mount not found in device graph"))?;

    if disk.is_system_disk {
        return Err(anyhow!("refusing to target system disk: {}", disk.id));
    }
    if !disk.removable {
        return Err(anyhow!(
            "target disk is not marked removable: {}",
            disk.id
        ));
    }

    let prepared = prepare_source(&params.source_path)?;
    let source_root = prepared.root.clone();
    if !source_root.is_dir() {
        return Err(anyhow!("source root is not a directory"));
    }

    let candidates = boot_prep_candidates(current_os(), &source_root)?;
    if candidates.is_empty() {
        return Err(anyhow!("no boot prep candidates found in source"));
    }

    let mut logs = Vec::new();
    logs.push("workflow=unix-boot-prep".to_string());
    logs.push(format!("target_disk={}", disk.id));
    logs.push(format!("target_mount={}", target_mount.display()));
    logs.push(format!("source_path={}", source_root.display()));

    let mut copied_files = 0usize;
    let mut copied_bytes = 0u64;
    let mut artifacts = Vec::new();
    let mut artifact_names = Vec::new();

    if !params.dry_run {
        let ctx = SafetyContext {
            force_mode: params.force,
            confirmation_token: params.confirmation_token.clone(),
        };
        match can_write_to_disk(&ctx, disk.is_system_disk) {
            SafetyDecision::Allow => {}
            SafetyDecision::Deny(reason) => return Err(anyhow!(reason)),
        }

        let test_path = target_mount.join(".phoenix_write_test");
        fs::write(&test_path, b"")?;
        fs::remove_file(&test_path).ok();
        logs.push("write_test=ok".to_string());

        let mut copy_manifest = Vec::new();
        for candidate in candidates {
            let target_path = target_mount.join(&candidate.relative);
            if target_path.exists() {
                logs.push(format!("skip_existing={}", candidate.relative));
                continue;
            }

            if candidate.is_dir {
                let stats = copy_dir_recursive(&candidate.source, &target_path, params.hash_manifest)?;
                copied_files += stats.files;
                copied_bytes += stats.bytes;
                copy_manifest.extend(stats.manifest);
            } else {
                if let Some(parent) = target_path.parent() {
                    fs::create_dir_all(parent)?;
                }
                fs::copy(&candidate.source, &target_path)?;
                copied_files += 1;
                let size = fs::metadata(&candidate.source)?.len();
                copied_bytes = copied_bytes.saturating_add(size);
                if params.hash_manifest {
                    let hash = hash_file(&candidate.source)?;
                    copy_manifest.push(CopyManifestEntry {
                        path: candidate.relative.to_string(),
                        bytes: size,
                        sha256: hash,
                    });
                }
            }
            logs.push(format!("copied={}", candidate.relative));
        }

        if params.hash_manifest && !copy_manifest.is_empty() {
            let bytes = serde_json::to_vec_pretty(&copy_manifest)?;
            artifacts.push(ReportArtifact {
                name: "bootprep_manifest.json".to_string(),
                bytes,
            });
            artifact_names.push("bootprep_manifest.json".to_string());
        }
    } else {
        logs.push("dry_run=true".to_string());
    }

    let meta = serde_json::json!({
        "workflow": "unix-boot-prep",
        "status": if params.dry_run { "dry_run" } else { "completed" },
        "target_disk_id": disk.id,
        "target_mount": target_mount.display().to_string(),
        "source_path": source_root.display().to_string(),
        "copied_files": copied_files,
        "copied_bytes": copied_bytes,
        "artifacts": artifact_names,
        "dry_run": params.dry_run
    });

    let report = create_report_bundle_with_meta_signing_and_artifacts(
        &params.report_base,
        &graph,
        Some(meta),
        Some(&logs.join("\n")),
        signing_key_from_env().as_deref(),
        &artifacts,
    )?;

    Ok(UnixBootPrepResult {
        report,
        copied_files,
        copied_bytes,
        dry_run: params.dry_run,
    })
}

#[derive(Debug, Clone)]
pub struct WorkflowStepResult {
    pub id: String,
    pub action: String,
    pub report_root: Option<PathBuf>,
    pub duration_ms: u128,
}

#[derive(Debug, Clone)]
pub struct WorkflowRunResult {
    pub report: ReportPaths,
    pub steps: Vec<WorkflowStepResult>,
}

pub fn run_workflow_definition(
    definition: &WorkflowDefinition,
    default_report_base: Option<PathBuf>,
) -> Result<Vec<WorkflowStepResult>> {
    validate_workflow_definition(definition)?;
    let base = default_report_base.unwrap_or_else(|| PathBuf::from("."));
    let mut results = Vec::new();

    for step in &definition.steps {
        let start = Instant::now();
        match step.action.as_str() {
            "windows_installer_usb" => {
                let params = build_usb_params(&step.params, &base)?;
                let result = run_windows_installer_usb(&params)?;
                results.push(WorkflowStepResult {
                    id: step.id.clone(),
                    action: step.action.clone(),
                    report_root: Some(result.report.root),
                    duration_ms: start.elapsed().as_millis(),
                });
            }
            "windows_apply_image" => {
                let params = build_apply_params(&step.params, &base)?;
                let result = run_windows_apply_image(&params)?;
                results.push(WorkflowStepResult {
                    id: step.id.clone(),
                    action: step.action.clone(),
                    report_root: Some(result.report.root),
                    duration_ms: start.elapsed().as_millis(),
                });
            }
            "linux_installer_usb" => {
                let params = build_unix_usb_params(&step.params, &base)?;
                let result = run_unix_installer_usb(&params)?;
                results.push(WorkflowStepResult {
                    id: step.id.clone(),
                    action: step.action.clone(),
                    report_root: Some(result.report.root),
                    duration_ms: start.elapsed().as_millis(),
                });
            }
            "macos_installer_usb" => {
                let params = build_unix_usb_params(&step.params, &base)?;
                let result = run_unix_installer_usb(&params)?;
                results.push(WorkflowStepResult {
                    id: step.id.clone(),
                    action: step.action.clone(),
                    report_root: Some(result.report.root),
                    duration_ms: start.elapsed().as_millis(),
                });
            }
            "linux_write_image" => {
                let params = build_unix_write_params(&step.params, &base)?;
                let result = run_unix_write_image(&params)?;
                results.push(WorkflowStepResult {
                    id: step.id.clone(),
                    action: step.action.clone(),
                    report_root: Some(result.report.root),
                    duration_ms: start.elapsed().as_millis(),
                });
            }
            "macos_write_image" => {
                let params = build_unix_write_params(&step.params, &base)?;
                let result = run_unix_write_image(&params)?;
                results.push(WorkflowStepResult {
                    id: step.id.clone(),
                    action: step.action.clone(),
                    report_root: Some(result.report.root),
                    duration_ms: start.elapsed().as_millis(),
                });
            }
            "linux_boot_prep" => {
                let params = build_unix_boot_params(&step.params, &base)?;
                let result = run_unix_boot_prep(&params)?;
                results.push(WorkflowStepResult {
                    id: step.id.clone(),
                    action: step.action.clone(),
                    report_root: Some(result.report.root),
                    duration_ms: start.elapsed().as_millis(),
                });
            }
            "macos_boot_prep" => {
                let params = build_unix_boot_params(&step.params, &base)?;
                let result = run_unix_boot_prep(&params)?;
                results.push(WorkflowStepResult {
                    id: step.id.clone(),
                    action: step.action.clone(),
                    report_root: Some(result.report.root),
                    duration_ms: start.elapsed().as_millis(),
                });
            }
            "macos_installer_usb" => {
                let params = build_macos_installer_params(&step.params, &base)?;
                let result = run_macos_installer_usb(&params)?;
                results.push(WorkflowStepResult {
                    id: step.id.clone(),
                    action: step.action.clone(),
                    report_root: Some(result.report.root),
                    duration_ms: start.elapsed().as_millis(),
                });
            }
            "stage_bootloader" => {
                let params = build_stage_bootloader_params(&step.params, &base)?;
                let result = run_stage_bootloader(&params)?;
                results.push(WorkflowStepResult {
                    id: step.id.clone(),
                    action: step.action.clone(),
                    report_root: Some(result.report.root),
                    duration_ms: start.elapsed().as_millis(),
                });
            }
            "macos_legacy_patch" => {
                let params = build_legacy_patch_params(&step.params, &base)?;
                let result = phoenix_legacy_patcher::run_legacy_patch(&params)?;
                results.push(WorkflowStepResult {
                    id: step.id.clone(),
                    action: step.action.clone(),
                    report_root: Some(result.report.root),
                    duration_ms: start.elapsed().as_millis(),
                });
            }
            "report_verify" => {
                let (path, key) = build_verify_params(&step.params)?;
                let verification = phoenix_report::verify_report_bundle(path, key.as_deref())?;
                if !verification.ok {
                    return Err(anyhow!("report verification failed"));
                }
                results.push(WorkflowStepResult {
                    id: step.id.clone(),
                    action: step.action.clone(),
                    report_root: None,
                    duration_ms: start.elapsed().as_millis(),
                });
            }
            "disk_hash_report" => {
                let params = build_hash_params(&step.params, &base)?;
                let result = run_disk_hash_report(&params)?;
                results.push(WorkflowStepResult {
                    id: step.id.clone(),
                    action: step.action.clone(),
                    report_root: Some(result.report.root),
                    duration_ms: start.elapsed().as_millis(),
                });
            }
            other => {
                return Err(anyhow!("unknown workflow action {}", other));
            }
        }
    }

    Ok(results)
}

pub fn run_workflow_definition_with_report(
    definition: &WorkflowDefinition,
    report_base: PathBuf,
) -> Result<WorkflowRunResult> {
    validate_workflow_definition(definition)?;
    let steps = run_workflow_definition(definition, Some(report_base.clone()))?;
    let graph = build_device_graph()?;

    let step_meta: Vec<serde_json::Value> = steps
        .iter()
        .map(|step| {
            serde_json::json!({
                "id": step.id,
                "action": step.action,
                "duration_ms": step.duration_ms,
                "report_root": step.report_root.as_ref().map(|p| p.display().to_string())
            })
        })
        .collect();

    let mut logs = Vec::new();
    logs.push(format!("workflow={}", definition.name));
    for step in &steps {
        logs.push(format!(
            "step={} action={} duration_ms={}",
            step.id, step.action, step.duration_ms
        ));
    }

    let meta = serde_json::json!({
        "workflow": definition.name,
        "schema_version": definition.schema_version,
        "steps": step_meta
    });

    let report = create_report_bundle_with_meta_and_signing(
        &report_base,
        &graph,
        Some(meta),
        Some(&logs.join("\n")),
        signing_key_from_env().as_deref(),
    )?;

    Ok(WorkflowRunResult { report, steps })
}

pub fn validate_workflow_definition(definition: &WorkflowDefinition) -> Result<()> {
    if definition.schema_version != WORKFLOW_SCHEMA_VERSION {
        return Err(anyhow!(
            "unsupported workflow schema version {}",
            definition.schema_version
        ));
    }
    if definition.steps.is_empty() {
        return Err(anyhow!("workflow has no steps"));
    }

    let mut seen = std::collections::HashSet::new();
    for step in &definition.steps {
        if step.id.trim().is_empty() {
            return Err(anyhow!("workflow step id is empty"));
        }
        if !seen.insert(step.id.clone()) {
            return Err(anyhow!("duplicate step id {}", step.id));
        }
        validate_step(step)?;
    }
    Ok(())
}

fn validate_step(step: &phoenix_core::WorkflowStep) -> Result<()> {
    match step.action.as_str() {
        "windows_installer_usb" => {
            ensure_os("windows")?;
            require_string(&step.params, "target_disk_id")?;
            require_string(&step.params, "source_path")?;
        }
        "windows_apply_image" => {
            ensure_os("windows")?;
            require_string(&step.params, "source_path")?;
            require_u32(&step.params, "image_index")?;
            require_string(&step.params, "target_dir")?;
        }
        "linux_installer_usb" => {
            ensure_os("linux")?;
            require_string(&step.params, "source_path")?;
            require_string(&step.params, "target_mount")?;
        }
        "macos_installer_usb" => {
            ensure_os("macos")?;
            require_string(&step.params, "source_path")?;
            require_string(&step.params, "target_mount")?;
        }
        "linux_write_image" => {
            ensure_os("linux")?;
            require_string(&step.params, "source_image")?;
            require_string(&step.params, "target_device")?;
        }
        "macos_write_image" => {
            ensure_os("macos")?;
            require_string(&step.params, "source_image")?;
            require_string(&step.params, "target_device")?;
        }
        "linux_boot_prep" => {
            ensure_os("linux")?;
            require_string(&step.params, "source_path")?;
            require_string(&step.params, "target_mount")?;
        }
        "macos_boot_prep" => {
            ensure_os("macos")?;
            require_string(&step.params, "source_path")?;
            require_string(&step.params, "target_mount")?;
        }
        "stage_bootloader" => {
            require_string(&step.params, "source_path")?;
            require_string(&step.params, "target_mount")?;
        }
        "macos_installer_usb" => {
            ensure_os("macos")?;
            require_string(&step.params, "source_path")?;
            require_string(&step.params, "target_device")?;
        }
        "macos_legacy_patch" => {
            ensure_os("macos")?;
            require_string(&step.params, "source_path")?;
        }
        "report_verify" => {
            require_string(&step.params, "path")?;
        }
        "disk_hash_report" => {
            require_string(&step.params, "disk_id")?;
        }
        other => {
            return Err(anyhow!("unknown workflow action {}", other));
        }
    }
    Ok(())
}

fn ensure_os(required: &str) -> Result<()> {
    let current = current_os();
    if current != required {
        return Err(anyhow!("action requires {}, current {}", required, current));
    }
    Ok(())
}

fn current_os() -> &'static str {
    if cfg!(target_os = "windows") {
        "windows"
    } else if cfg!(target_os = "linux") {
        "linux"
    } else if cfg!(target_os = "macos") {
        "macos"
    } else {
        "unknown"
    }
}

#[derive(Debug, Clone)]
pub struct WindowsApplyImageParams {
    pub source_path: PathBuf,
    pub image_index: u32,
    pub target_dir: PathBuf,
    pub report_base: PathBuf,
    pub force: bool,
    pub confirmation_token: Option<String>,
    pub dry_run: bool,
    pub verify: bool,
}

#[derive(Debug, Clone)]
pub struct WindowsApplyImageResult {
    pub report: ReportPaths,
    pub target_dir: PathBuf,
    pub file_count: usize,
    pub total_bytes: u64,
    pub dry_run: bool,
}

pub struct WindowsApplyImageWorkflow {
    params: WindowsApplyImageParams,
}

impl WindowsApplyImageWorkflow {
    pub fn new(params: WindowsApplyImageParams) -> Self {
        Self { params }
    }

    pub fn execute(&self) -> Result<WindowsApplyImageResult> {
        run_windows_apply_image(&self.params)
    }
}

impl Workflow for WindowsApplyImageWorkflow {
    fn name(&self) -> &'static str {
        "windows-apply-image"
    }

    fn run(&self) -> Result<()> {
        self.execute().map(|_| ())
    }
}

pub fn run_windows_apply_image(params: &WindowsApplyImageParams) -> Result<WindowsApplyImageResult> {
    let graph = build_device_graph()?;
    let is_system_target = is_system_mount_path(&params.target_dir, &graph);

    let (image_path, _prepared) = resolve_windows_image(&params.source_path)?;
    let images = wim_list_images(&image_path)?;
    let image_info = images
        .iter()
        .find(|image| image.index == params.image_index)
        .ok_or_else(|| anyhow!("image index not found"))?;

    let mut logs = Vec::new();
    logs.push("workflow=windows-apply-image".to_string());
    logs.push(format!("image_path={}", image_path.display()));
    logs.push(format!("image_index={}", params.image_index));
    logs.push(format!("target_dir={}", params.target_dir.display()));
    logs.push(format!("dry_run={}", params.dry_run));

    if !params.dry_run {
        let ctx = SafetyContext {
            force_mode: params.force,
            confirmation_token: params.confirmation_token.clone(),
        };
        match can_write_to_disk(&ctx, is_system_target) {
            SafetyDecision::Allow => {}
            SafetyDecision::Deny(reason) => return Err(anyhow!(reason)),
        }

        if !params.target_dir.exists() {
            fs::create_dir_all(&params.target_dir).context("create target dir")?;
        }
        if let Some(expected) = image_info.total_bytes {
            if let Ok(free_bytes) = free_space_bytes(&params.target_dir.display().to_string()) {
                if free_bytes < expected {
                    return Err(anyhow!(
                        "insufficient free space: required {}, available {}",
                        expected,
                        free_bytes
                    ));
                }
            }
        }
        wim_apply_image(&image_path, params.image_index, &params.target_dir)?;
        logs.push("apply_complete".to_string());
    } else {
        logs.push("apply_skipped_dry_run".to_string());
    }

    let stats = if params.verify && !params.dry_run {
        let stats = dir_stats(&params.target_dir)?;
        if let Some(expected) = image_info.total_bytes {
            let tolerance = expected / 100;
            if stats.total_bytes + tolerance < expected {
                return Err(anyhow!(
                    "verification failed: bytes {} < expected {}",
                    stats.total_bytes,
                    expected
                ));
            }
        }
        logs.push(format!("verified_files={}", stats.file_count));
        logs.push(format!("verified_bytes={}", stats.total_bytes));
        stats
    } else {
        DirStats {
            file_count: 0,
            total_bytes: 0,
        }
    };

    let meta = serde_json::json!({
        "workflow": "windows-apply-image",
        "status": if params.dry_run { "dry_run" } else { "completed" },
        "image_path": image_path.display().to_string(),
        "image_index": params.image_index,
        "image_name": image_info.name,
        "image_description": image_info.description,
        "target_dir": params.target_dir.display().to_string(),
        "verify": params.verify,
        "file_count": stats.file_count,
        "total_bytes": stats.total_bytes,
        "dry_run": params.dry_run
    });

    let report = create_report_bundle_with_meta_and_signing(
        &params.report_base,
        &graph,
        Some(meta),
        Some(&logs.join("\n")),
        signing_key_from_env().as_deref(),
    )?;

    Ok(WindowsApplyImageResult {
        report,
        target_dir: params.target_dir.clone(),
        file_count: stats.file_count,
        total_bytes: stats.total_bytes,
        dry_run: params.dry_run,
    })
}

#[derive(Debug, Clone)]
pub struct DiskHashReportParams {
    pub disk_id: String,
    pub chunk_size: u64,
    pub max_chunks: Option<u64>,
    pub report_base: PathBuf,
}

#[derive(Debug, Clone)]
pub struct DiskHashReportResult {
    pub report: ReportPaths,
    pub disk_id: String,
    pub chunk_count: usize,
}

pub fn run_disk_hash_report(params: &DiskHashReportParams) -> Result<DiskHashReportResult> {
    let graph = build_device_graph()?;
    let disk = graph
        .disks
        .iter()
        .find(|disk| disk.id.eq_ignore_ascii_case(&params.disk_id))
        .ok_or_else(|| anyhow!("disk not found: {}", params.disk_id))?;

    let plan = make_chunk_plan(disk.size_bytes, params.chunk_size);
    let hashes = {
        #[cfg(target_os = "windows")]
        {
            hash_disk_readonly_physicaldrive(
                &disk.id,
                disk.size_bytes,
                params.chunk_size,
                params.max_chunks,
            )?
        }
        #[cfg(not(target_os = "windows"))]
        {
            let device_path = format!("/dev/{}", disk.id);
            hash_device_readonly(
                &device_path,
                disk.size_bytes,
                params.chunk_size,
                params.max_chunks,
            )?
        }
    };

    let entries: Vec<DiskHashEntry> = hashes
        .into_iter()
        .filter_map(|(index, sha256)| {
            let chunk = plan.get(index as usize)?;
            Some(DiskHashEntry {
                index,
                offset: chunk.offset,
                length: chunk.size,
                sha256,
            })
        })
        .collect();

    let artifact = ReportArtifact {
        name: "disk_hashes.json".to_string(),
        bytes: serde_json::to_vec_pretty(&entries)?,
    };

    let meta = serde_json::json!({
        "workflow": "disk-hash-report",
        "disk_id": disk.id,
        "chunk_size": params.chunk_size,
        "chunk_count": entries.len()
    });

    let report = create_report_bundle_with_meta_signing_and_artifacts(
        &params.report_base,
        &graph,
        Some(meta),
        None,
        signing_key_from_env().as_deref(),
        &[artifact],
    )?;

    Ok(DiskHashReportResult {
        report,
        disk_id: disk.id.clone(),
        chunk_count: entries.len(),
    })
}

#[derive(Debug)]
struct FileEntry {
    absolute_path: PathBuf,
    relative_path: PathBuf,
    size: u64,
}

fn collect_files(root: &Path) -> Result<Vec<FileEntry>> {
    let mut entries = Vec::new();
    collect_files_inner(root, root, &mut entries)?;
    Ok(entries)
}

fn collect_files_inner(root: &Path, current: &Path, entries: &mut Vec<FileEntry>) -> Result<()> {
    for entry in fs::read_dir(current).with_context(|| format!("read {}", current.display()))? {
        let entry = entry?;
        let path = entry.path();
        let metadata = entry.metadata()?;
        if metadata.is_dir() {
            collect_files_inner(root, &path, entries)?;
        } else if metadata.is_file() {
            let relative_path = path
                .strip_prefix(root)
                .map(PathBuf::from)
                .context("strip source prefix")?;
            entries.push(FileEntry {
                absolute_path: path,
                relative_path,
                size: metadata.len(),
            });
        }
    }
    Ok(())
}

fn verify_copy(target_root: &Path, entries: &[FileEntry]) -> Result<()> {
    for entry in entries {
        let dest_path = target_root.join(&entry.relative_path);
        let metadata = fs::metadata(&dest_path).with_context(|| {
            format!("verify missing file {}", dest_path.display())
        })?;
        if metadata.len() != entry.size {
            return Err(anyhow!(
                "verify failed for {} (expected {}, got {})",
                dest_path.display(),
                entry.size,
                metadata.len()
            ));
        }
    }
    Ok(())
}

fn normalize_mount_path(path: &Path) -> PathBuf {
    let mut value = path.display().to_string();
    if value.len() == 2 && value.ends_with(':') {
        value.push('\\');
    }
    if value.len() == 3 && value.ends_with(":\\") {
        return PathBuf::from(value);
    }
    if !value.ends_with('\\') && value.ends_with(':') {
        value.push('\\');
    }
    PathBuf::from(value)
}

fn parse_disk_number(id: &str) -> Option<u32> {
    let suffix = id.strip_prefix("PhysicalDrive")?;
    suffix.parse().ok()
}

fn extract_drive_letter(path: &Path) -> Option<char> {
    let value = path.display().to_string();
    let mut chars = value.chars();
    let first = chars.next()?;
    if chars.next() == Some(':') {
        Some(first.to_ascii_uppercase())
    } else {
        None
    }
}

fn is_system_mount_path(path: &Path, graph: &phoenix_core::DeviceGraph) -> bool {
    let value = normalize_mount_path(path).display().to_string();
    graph.disks.iter().any(|disk| {
        disk.is_system_disk
            && disk
                .partitions
                .iter()
                .flat_map(|partition| partition.mount_points.iter())
                .any(|mount| mount.eq_ignore_ascii_case(&value))
    })
}

#[derive(Debug)]
struct DirStats {
    file_count: usize,
    total_bytes: u64,
}

fn dir_stats(root: &Path) -> Result<DirStats> {
    let mut stats = DirStats {
        file_count: 0,
        total_bytes: 0,
    };
    dir_stats_inner(root, &mut stats)?;
    Ok(stats)
}

fn dir_stats_inner(path: &Path, stats: &mut DirStats) -> Result<()> {
    for entry in fs::read_dir(path).with_context(|| format!("read {}", path.display()))? {
        let entry = entry?;
        let meta = entry.metadata()?;
        if meta.is_dir() {
            dir_stats_inner(&entry.path(), stats)?;
        } else if meta.is_file() {
            stats.file_count += 1;
            stats.total_bytes = stats.total_bytes.saturating_add(meta.len());
        }
    }
    Ok(())
}

fn signing_key_from_env() -> Option<String> {
    std::env::var("PHOENIX_SIGNING_KEY").ok()
}

fn normalize_mount_for_unix(path: &Path) -> PathBuf {
    let mut value = path.display().to_string();
    if value != "/" {
        while value.ends_with('/') {
            value.pop();
        }
    }
    PathBuf::from(value)
}

fn find_disk_by_mount<'a>(graph: &'a DeviceGraph, mount: &Path) -> Option<&'a phoenix_core::Disk> {
    let mount_str = normalize_mount_for_unix(mount).display().to_string();
    graph.disks.iter().find(|disk| {
        disk.partitions.iter().any(|partition| {
            partition.mount_points.iter().any(|mp| {
                let candidate = normalize_mount_for_unix(&PathBuf::from(mp)).display().to_string();
                candidate == mount_str
            })
        })
    })
}

fn disk_id_from_device_path(path: &Path) -> Option<String> {
    let name = path.file_name()?.to_string_lossy().to_string();
    if name.starts_with("disk") {
        if let Some(idx) = name.find('s') {
            return Some(name[..idx].to_string());
        }
        return Some(name);
    }
    if name.starts_with("nvme") && name.contains('p') {
        if let Some(idx) = name.rfind('p') {
            return Some(name[..idx].to_string());
        }
    }
    let trimmed = name.trim_end_matches(|c: char| c.is_ascii_digit()).to_string();
    if trimmed.is_empty() {
        None
    } else {
        Some(trimmed)
    }
}

fn select_macos_fs(version: &str) -> Option<String> {
    let normalized = version.trim().to_ascii_lowercase();
    let (major, minor) = parse_macos_version(&normalized)?;
    if major > 10 || (major == 10 && minor >= 13) {
        Some("APFS".to_string())
    } else {
        Some("JHFS+".to_string())
    }
}

fn parse_macos_version(value: &str) -> Option<(u32, u32)> {
    if let Some((major, minor)) = parse_numeric_version(value) {
        return Some((major, minor));
    }

    let name = value.replace('-', " ").trim().to_string();
    let map = [
        ("snow leopard", (10, 6)),
        ("lion", (10, 7)),
        ("mountain lion", (10, 8)),
        ("mavericks", (10, 9)),
        ("yosemite", (10, 10)),
        ("el capitan", (10, 11)),
        ("sierra", (10, 12)),
        ("high sierra", (10, 13)),
        ("mojave", (10, 14)),
        ("catalina", (10, 15)),
        ("big sur", (11, 0)),
        ("monterey", (12, 0)),
        ("ventura", (13, 0)),
        ("sonoma", (14, 0)),
        ("sequoia", (15, 0)),
        ("tahoe", (26, 0)),
    ];
    for (label, version) in map {
        if name.contains(label) {
            return Some(version);
        }
    }
    None
}

fn parse_numeric_version(value: &str) -> Option<(u32, u32)> {
    let parts: Vec<&str> = value.split('.').collect();
    if parts.is_empty() {
        return None;
    }
    let major = parts.get(0)?.parse::<u32>().ok()?;
    let minor = parts.get(1).and_then(|v| v.parse::<u32>().ok()).unwrap_or(0);
    Some((major, minor))
}

#[cfg(target_os = "macos")]
fn is_macos_app(path: &Path) -> bool {
    path.extension()
        .and_then(|ext| ext.to_str())
        .map(|ext| ext.eq_ignore_ascii_case("app"))
        .unwrap_or(false)
        && path.join("Contents/Resources/createinstallmedia").exists()
}

#[cfg(target_os = "macos")]
struct MountedDmg {
    mount_point: PathBuf,
}

#[cfg(target_os = "macos")]
impl Drop for MountedDmg {
    fn drop(&mut self) {
        let _ = run_cmd(
            "/usr/bin/hdiutil",
            &["detach", self.mount_point.to_string_lossy().as_ref()],
        );
    }
}

#[cfg(target_os = "macos")]
fn mount_dmg(path: &Path) -> Result<MountedDmg> {
    let mount_point = std::env::temp_dir().join(format!(
        "phoenix_dmg_{}",
        std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .unwrap_or_default()
            .as_secs()
    ));
    fs::create_dir_all(&mount_point)?;
    run_cmd(
        "/usr/bin/hdiutil",
        &[
            "attach",
            path.to_string_lossy().as_ref(),
            "-nobrowse",
            "-readonly",
            "-mountpoint",
            mount_point.to_string_lossy().as_ref(),
        ],
    )?;
    Ok(MountedDmg { mount_point })
}

#[cfg(target_os = "macos")]
fn find_install_app(root: &Path) -> Option<PathBuf> {
    let entries = fs::read_dir(root).ok()?;
    for entry in entries.flatten() {
        let path = entry.path();
        if is_macos_app(&path) {
            return Some(path);
        }
    }
    None
}

#[cfg(target_os = "macos")]
fn erase_disk(target_device: &Path, fs: &str, name: &str) -> Result<()> {
    run_cmd(
        "/usr/sbin/diskutil",
        &[
            "eraseDisk",
            fs,
            name,
            target_device.to_string_lossy().as_ref(),
        ],
    )
}

#[cfg(target_os = "macos")]
fn run_createinstallmedia(app: &Path, target_volume: &Path) -> Result<()> {
    let tool = app.join("Contents/Resources/createinstallmedia");
    if !tool.exists() {
        return Err(anyhow!("createinstallmedia not found"));
    }
    run_cmd(
        tool.to_string_lossy().as_ref(),
        &[
            "--volume",
            target_volume.to_string_lossy().as_ref(),
            "--nointeraction",
        ],
    )
}

#[cfg(target_os = "macos")]
fn run_asr_restore(source: &Path, target_device: &Path) -> Result<()> {
    run_cmd(
        "/usr/sbin/asr",
        &[
            "restore",
            "--source",
            source.to_string_lossy().as_ref(),
            "--target",
            target_device.to_string_lossy().as_ref(),
            "--erase",
            "--noprompt",
        ],
    )
}

#[cfg(target_os = "macos")]
fn run_cmd(cmd: &str, args: &[&str]) -> Result<()> {
    let output = std::process::Command::new(cmd)
        .args(args)
        .output()
        .with_context(|| format!("run {}", cmd))?;
    if output.status.success() {
        Ok(())
    } else {
        Err(anyhow!(
            "{} failed: {}",
            cmd,
            String::from_utf8_lossy(&output.stderr)
        ))
    }
}

#[cfg(not(target_os = "macos"))]
fn run_cmd(_cmd: &str, _args: &[&str]) -> Result<()> {
    Err(anyhow!("macos tool requires macOS"))
}

fn free_space_bytes(path: &Path) -> Result<Option<u64>> {
    #[cfg(unix)]
    {
        use libc::statvfs;
        use std::ffi::CString;
        use std::mem::MaybeUninit;

        let c_path = CString::new(path.display().to_string())
            .map_err(|_| anyhow!("invalid path"))?;
        let mut stats = MaybeUninit::zeroed();
        let result = unsafe { statvfs(c_path.as_ptr(), stats.as_mut_ptr()) };
        if result != 0 {
            return Ok(None);
        }
        let stats = unsafe { stats.assume_init() };
        let free = (stats.f_bavail as u64).saturating_mul(stats.f_frsize as u64);
        Ok(Some(free))
    }
    #[cfg(not(unix))]
    {
        let _ = path;
        Ok(None)
    }
}

fn build_device_graph() -> Result<DeviceGraph> {
    #[cfg(target_os = "windows")]
    {
        return phoenix_host_windows::build_device_graph();
    }
    #[cfg(target_os = "linux")]
    {
        return phoenix_host_linux::build_device_graph();
    }
    #[cfg(target_os = "macos")]
    {
        return phoenix_host_macos::build_device_graph();
    }
    #[cfg(not(any(target_os = "windows", target_os = "linux", target_os = "macos")))]
    {
        Err(anyhow!("unsupported OS"))
    }
}

const FAT32_MAX_FILE: u64 = 4_294_967_295;

fn max_file_size(entries: &[FileEntry]) -> u64 {
    entries.iter().map(|entry| entry.size).max().unwrap_or(0)
}

#[derive(serde::Serialize)]
struct CopyManifestEntry {
    path: String,
    bytes: u64,
    sha256: String,
}

#[derive(serde::Serialize)]
struct DiskHashEntry {
    index: u64,
    offset: u64,
    length: u64,
    sha256: String,
}

fn ensure_boot_files(entries: &[FileEntry]) -> Result<()> {
    let mut has_boot_wim = false;
    let mut has_efi = false;
    for entry in entries {
        let rel = entry.relative_path.to_string_lossy().replace('\\', "/");
        let rel_lower = rel.to_ascii_lowercase();
        if rel_lower == "sources/boot.wim" {
            has_boot_wim = true;
        }
        if rel_lower.starts_with("efi/boot/") && rel_lower.ends_with(".efi") {
            has_efi = true;
        }
    }
    if !has_boot_wim {
        return Err(anyhow!("missing sources/boot.wim in installer source"));
    }
    if !has_efi {
        return Err(anyhow!("missing EFI bootloader in installer source"));
    }
    Ok(())
}

fn ensure_unix_boot_files(entries: &[FileEntry], os: &str) -> Result<()> {
    let mut has_efi = false;
    let mut has_grub = false;
    let mut has_isolinux = false;
    let mut has_macos_boot = false;
    for entry in entries {
        let rel = entry.relative_path.to_string_lossy().replace('\\', "/");
        let rel_lower = rel.to_ascii_lowercase();
        if rel_lower.starts_with("efi/boot/") {
            has_efi = true;
        }
        if rel_lower.starts_with("boot/grub") {
            has_grub = true;
        }
        if rel_lower.starts_with("isolinux/") {
            has_isolinux = true;
        }
        if rel_lower == "system/library/coreservices/boot.efi" {
            has_macos_boot = true;
        }
    }

    match os {
        "linux" => {
            if !has_efi && !has_grub && !has_isolinux {
                return Err(anyhow!(
                    "linux source missing EFI/BOOT, boot/grub, or isolinux"
                ));
            }
        }
        "macos" => {
            if !has_macos_boot && !has_efi {
                return Err(anyhow!(
                    "macos source missing System/Library/CoreServices/boot.efi or EFI/BOOT"
                ));
            }
        }
        _ => {}
    }
    Ok(())
}

#[derive(Debug, Clone)]
struct BootCandidate {
    source: PathBuf,
    relative: String,
    is_dir: bool,
}

fn boot_prep_candidates(os: &str, source_root: &Path) -> Result<Vec<BootCandidate>> {
    let mut candidates = Vec::new();
    match os {
        "linux" => {
            add_candidate_dir(&mut candidates, source_root, "EFI/BOOT");
            add_candidate_dir(&mut candidates, source_root, "boot/grub");
            add_candidate_dir(&mut candidates, source_root, "isolinux");
        }
        "macos" => {
            add_candidate_file(
                &mut candidates,
                source_root,
                "System/Library/CoreServices/boot.efi",
            );
            add_candidate_dir(&mut candidates, source_root, "EFI/BOOT");
        }
        _ => {}
    }
    Ok(candidates)
}

fn add_candidate_dir(candidates: &mut Vec<BootCandidate>, root: &Path, rel: &str) {
    let path = root.join(rel);
    if path.is_dir() {
        candidates.push(BootCandidate {
            source: path,
            relative: rel.replace('\\', "/"),
            is_dir: true,
        });
    }
}

fn add_candidate_file(candidates: &mut Vec<BootCandidate>, root: &Path, rel: &str) {
    let path = root.join(rel);
    if path.is_file() {
        candidates.push(BootCandidate {
            source: path,
            relative: rel.replace('\\', "/"),
            is_dir: false,
        });
    }
}

#[derive(Default)]
struct CopyStats {
    files: usize,
    bytes: u64,
    manifest: Vec<CopyManifestEntry>,
}

fn copy_dir_recursive(
    source: &Path,
    dest: &Path,
    hash_manifest: bool,
) -> Result<CopyStats> {
    let mut stats = CopyStats::default();
    copy_dir_recursive_inner(source, dest, source, hash_manifest, &mut stats)?;
    Ok(stats)
}

fn copy_dir_recursive_inner(
    source_root: &Path,
    dest_root: &Path,
    current: &Path,
    hash_manifest: bool,
    stats: &mut CopyStats,
) -> Result<()> {
    for entry in fs::read_dir(current)? {
        let entry = entry?;
        let path = entry.path();
        let metadata = entry.metadata()?;
        let relative = path
            .strip_prefix(source_root)
            .unwrap_or(&path)
            .to_string_lossy()
            .replace('\\', "/");
        let dest_path = dest_root.join(&relative);
        if metadata.is_dir() {
            fs::create_dir_all(&dest_path)?;
            copy_dir_recursive_inner(source_root, dest_root, &path, hash_manifest, stats)?;
        } else if metadata.is_file() {
            if let Some(parent) = dest_path.parent() {
                fs::create_dir_all(parent)?;
            }
            fs::copy(&path, &dest_path)?;
            stats.files += 1;
            stats.bytes = stats.bytes.saturating_add(metadata.len());
            if hash_manifest {
                let hash = hash_file(&path)?;
                stats.manifest.push(CopyManifestEntry {
                    path: relative,
                    bytes: metadata.len(),
                    sha256: hash,
                });
            }
        }
    }
    Ok(())
}

fn hash_file(path: &Path) -> Result<String> {
    use std::io::Read;
    let mut file = fs::File::open(path).with_context(|| format!("open {}", path.display()))?;
    let mut hasher = Sha256::new();
    let mut buffer = vec![0u8; 1024 * 1024];
    loop {
        let read = file.read(&mut buffer)?;
        if read == 0 {
            break;
        }
        hasher.update(&buffer[..read]);
    }
    Ok(to_hex(&hasher.finalize()))
}

fn to_hex(bytes: &[u8]) -> String {
    let mut out = String::with_capacity(bytes.len() * 2);
    for byte in bytes {
        out.push_str(&format!("{:02x}", byte));
    }
    out
}

fn default_driver_target() -> PathBuf {
    PathBuf::from(r"sources\$OEM$\$1\Drivers")
}

fn build_usb_params(value: &serde_json::Value, default_report: &Path) -> Result<WindowsInstallerUsbParams> {
    let target_disk_id = require_string(value, "target_disk_id")?;
    let source_path = PathBuf::from(require_string(value, "source_path")?);
    let report_base = PathBuf::from(optional_string(value, "report_base").unwrap_or_else(|| {
        default_report.display().to_string()
    }));
    let filesystem = parse_filesystem_value(optional_string(value, "filesystem").unwrap_or("fat32"))?;
    let label = optional_string(value, "label").map(str::to_string);

    Ok(WindowsInstallerUsbParams {
        target_disk_id: target_disk_id.to_string(),
        source_path,
        target_mount: optional_string(value, "target_mount").map(PathBuf::from),
        report_base,
        force: optional_bool(value, "force", false),
        confirmation_token: optional_string(value, "confirmation_token").map(str::to_string),
        dry_run: optional_bool(value, "dry_run", true),
        repartition: optional_bool(value, "repartition", false),
        format: optional_bool(value, "format", false),
        filesystem,
        label,
        driver_source: optional_string(value, "driver_source").map(PathBuf::from),
        driver_target: optional_string(value, "driver_target").map(PathBuf::from),
        hash_manifest: optional_bool(value, "hash_manifest", false),
    })
}

fn build_apply_params(value: &serde_json::Value, default_report: &Path) -> Result<WindowsApplyImageParams> {
    let source_path = PathBuf::from(require_string(value, "source_path")?);
    let target_dir = PathBuf::from(require_string(value, "target_dir")?);
    let report_base = PathBuf::from(optional_string(value, "report_base").unwrap_or_else(|| {
        default_report.display().to_string()
    }));
    let image_index = require_u32(value, "image_index")?;

    Ok(WindowsApplyImageParams {
        source_path,
        image_index,
        target_dir,
        report_base,
        force: optional_bool(value, "force", false),
        confirmation_token: optional_string(value, "confirmation_token").map(str::to_string),
        dry_run: optional_bool(value, "dry_run", true),
        verify: optional_bool(value, "verify", false),
    })
}

fn build_verify_params(value: &serde_json::Value) -> Result<(PathBuf, Option<String>)> {
    let path = PathBuf::from(require_string(value, "path")?);
    let key = optional_string(value, "signing_key").map(str::to_string);
    Ok((path, key))
}

fn build_hash_params(value: &serde_json::Value, default_report: &Path) -> Result<DiskHashReportParams> {
    let disk_id = require_string(value, "disk_id")?;
    let report_base = PathBuf::from(optional_string(value, "report_base").unwrap_or_else(|| {
        default_report.display().to_string()
    }));
    let chunk_size = value
        .get("chunk_size")
        .and_then(|v| v.as_u64())
        .unwrap_or(8 * 1024 * 1024);
    let max_chunks = value.get("max_chunks").and_then(|v| v.as_u64());

    Ok(DiskHashReportParams {
        disk_id: disk_id.to_string(),
        chunk_size,
        max_chunks,
        report_base,
    })
}

fn build_unix_usb_params(value: &serde_json::Value, default_report: &Path) -> Result<UnixInstallerUsbParams> {
    let source_path = PathBuf::from(require_string(value, "source_path")?);
    let target_mount = PathBuf::from(require_string(value, "target_mount")?);
    let report_base = PathBuf::from(optional_string(value, "report_base").unwrap_or_else(|| {
        default_report.display().to_string()
    }));

    Ok(UnixInstallerUsbParams {
        source_path,
        target_mount,
        report_base,
        force: optional_bool(value, "force", false),
        confirmation_token: optional_string(value, "confirmation_token").map(str::to_string),
        dry_run: optional_bool(value, "dry_run", true),
        hash_manifest: optional_bool(value, "hash_manifest", false),
        format_device: optional_string(value, "format_device").map(PathBuf::from),
        format_size_bytes: value.get("format_size_bytes").and_then(|v| v.as_u64()),
        format_label: optional_string(value, "format_label").map(str::to_string),
    })
}

fn build_unix_write_params(
    value: &serde_json::Value,
    default_report: &Path,
) -> Result<UnixWriteImageParams> {
    let source_image = PathBuf::from(require_string(value, "source_image")?);
    let target_device = PathBuf::from(require_string(value, "target_device")?);
    let report_base = PathBuf::from(optional_string(value, "report_base").unwrap_or_else(|| {
        default_report.display().to_string()
    }));
    let chunk_size = value
        .get("chunk_size")
        .and_then(|v| v.as_u64())
        .unwrap_or(8 * 1024 * 1024);

    Ok(UnixWriteImageParams {
        source_image,
        target_device,
        report_base,
        force: optional_bool(value, "force", false),
        confirmation_token: optional_string(value, "confirmation_token").map(str::to_string),
        dry_run: optional_bool(value, "dry_run", true),
        verify: optional_bool(value, "verify", false),
        chunk_size,
    })
}

fn build_unix_boot_params(
    value: &serde_json::Value,
    default_report: &Path,
) -> Result<UnixBootPrepParams> {
    let source_path = PathBuf::from(require_string(value, "source_path")?);
    let target_mount = PathBuf::from(require_string(value, "target_mount")?);
    let report_base = PathBuf::from(optional_string(value, "report_base").unwrap_or_else(|| {
        default_report.display().to_string()
    }));

    Ok(UnixBootPrepParams {
        source_path,
        target_mount,
        report_base,
        force: optional_bool(value, "force", false),
        confirmation_token: optional_string(value, "confirmation_token").map(str::to_string),
        dry_run: optional_bool(value, "dry_run", true),
        hash_manifest: optional_bool(value, "hash_manifest", false),
    })
}

fn build_macos_installer_params(
    value: &serde_json::Value,
    default_report: &Path,
) -> Result<MacosInstallerUsbParams> {
    let source_path = PathBuf::from(require_string(value, "source_path")?);
    let target_device = PathBuf::from(require_string(value, "target_device")?);
    let report_base = PathBuf::from(optional_string(value, "report_base").unwrap_or_else(|| {
        default_report.display().to_string()
    }));
    let volume_name = optional_string(value, "volume_name")
        .unwrap_or("PHOENIX-MACOS")
        .to_string();
    let macos_version = optional_string(value, "macos_version").map(str::to_string);
    let filesystem = optional_string(value, "filesystem").map(str::to_string);

    Ok(MacosInstallerUsbParams {
        source_path,
        target_device,
        report_base,
        volume_name,
        macos_version,
        filesystem,
        force: optional_bool(value, "force", false),
        confirmation_token: optional_string(value, "confirmation_token").map(str::to_string),
        dry_run: optional_bool(value, "dry_run", true),
    })
}

fn build_stage_bootloader_params(
    value: &serde_json::Value,
    default_report: &Path,
) -> Result<BootloaderStageParams> {
    let source_path = PathBuf::from(require_string(value, "source_path")?);
    let target_mount = PathBuf::from(require_string(value, "target_mount")?);
    let report_base = PathBuf::from(optional_string(value, "report_base").unwrap_or_else(|| {
        default_report.display().to_string()
    }));
    let target_subdir = optional_string(value, "target_subdir").map(PathBuf::from);

    Ok(BootloaderStageParams {
        source_path,
        target_mount,
        target_subdir,
        report_base,
        force: optional_bool(value, "force", false),
        confirmation_token: optional_string(value, "confirmation_token").map(str::to_string),
        dry_run: optional_bool(value, "dry_run", true),
        hash_manifest: optional_bool(value, "hash_manifest", false),
    })
}

fn build_legacy_patch_params(
    value: &serde_json::Value,
    default_report: &Path,
) -> Result<phoenix_legacy_patcher::LegacyPatchParams> {
    let source_path = PathBuf::from(require_string(value, "source_path")?);
    let report_base = PathBuf::from(optional_string(value, "report_base").unwrap_or_else(|| {
        default_report.display().to_string()
    }));
    Ok(phoenix_legacy_patcher::LegacyPatchParams {
        source_path,
        report_base,
        model: optional_string(value, "model").map(str::to_string),
        board_id: optional_string(value, "board_id").map(str::to_string),
        force: optional_bool(value, "force", false),
        confirmation_token: optional_string(value, "confirmation_token").map(str::to_string),
        dry_run: optional_bool(value, "dry_run", true),
    })
}

fn require_string<'a>(value: &'a serde_json::Value, key: &str) -> Result<&'a str> {
    value
        .get(key)
        .and_then(|v| v.as_str())
        .ok_or_else(|| anyhow!("missing string field {}", key))
}

fn optional_string<'a>(value: &'a serde_json::Value, key: &str) -> Option<&'a str> {
    value.get(key).and_then(|v| v.as_str())
}

fn require_u32(value: &serde_json::Value, key: &str) -> Result<u32> {
    value
        .get(key)
        .and_then(|v| v.as_u64())
        .map(|v| v as u32)
        .ok_or_else(|| anyhow!("missing number field {}", key))
}

fn optional_bool(value: &serde_json::Value, key: &str, default: bool) -> bool {
    value.get(key).and_then(|v| v.as_bool()).unwrap_or(default)
}

fn parse_filesystem_value(value: &str) -> Result<FileSystem> {
    match value.trim().to_ascii_lowercase().as_str() {
        "fat32" => Ok(FileSystem::Fat32),
        "ntfs" => Ok(FileSystem::Ntfs),
        "exfat" => Ok(FileSystem::ExFat),
        other => Err(anyhow!("unsupported filesystem {}", other)),
    }
}
