use anyhow::{anyhow, Context, Result};
use phoenix_report::{create_report_bundle_with_meta_and_signing, ReportPaths};
use phoenix_safety::{can_write_to_disk, SafetyContext, SafetyDecision};
use phoenix_content::{prepare_source, resolve_windows_image, SourceKind};
use phoenix_host_windows::format::{format_existing_volume, prepare_usb_disk, FileSystem};
use phoenix_wim::{apply_image as wim_apply_image, list_images as wim_list_images};
use phoenix_core::WorkflowDefinition;
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
}

#[derive(Debug, Clone)]
pub struct WindowsInstallerUsbResult {
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
    let graph = phoenix_host_windows::build_device_graph()?;
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
        }
        logs.push("copy_complete".to_string());

        verify_copy(&target_mount, &files)?;
        logs.push("verify_complete".to_string());
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
        "dry_run": params.dry_run
    });

    let report = create_report_bundle_with_meta_and_signing(
        &params.report_base,
        &graph,
        Some(meta),
        Some(&logs.join("\n")),
        signing_key_from_env().as_deref(),
    )?;

    Ok(WindowsInstallerUsbResult {
        report,
        target_mount,
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
    let steps = run_workflow_definition(definition, Some(report_base.clone()))?;
    let graph = phoenix_host_windows::build_device_graph()?;

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
    let graph = phoenix_host_windows::build_device_graph()?;
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

const FAT32_MAX_FILE: u64 = 4_294_967_295;

fn max_file_size(entries: &[FileEntry]) -> u64 {
    entries.iter().map(|entry| entry.size).max().unwrap_or(0)
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
