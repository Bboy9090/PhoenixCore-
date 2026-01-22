use anyhow::{anyhow, Context, Result};
use phoenix_report::{create_report_bundle_with_meta, ReportPaths};
use phoenix_safety::{can_write_to_disk, SafetyContext, SafetyDecision};
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

    let target_mount = if let Some(path) = &params.target_mount {
        normalize_mount_path(path)
    } else {
        disk.partitions
            .iter()
            .flat_map(|partition| partition.mount_points.iter())
            .next()
            .map(|mount| normalize_mount_path(&PathBuf::from(mount)))
            .ok_or_else(|| anyhow!("no mounted volume found for {}", disk.id))?
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

    let source_root =
        fs::canonicalize(&params.source_path).context("resolve source path")?;
    if !source_root.is_dir() {
        return Err(anyhow!("source path is not a directory"));
    }

    let setup_exe = source_root.join("setup.exe");
    if !setup_exe.exists() {
        return Err(anyhow!(
            "source missing setup.exe (provide extracted Windows installer files)"
        ));
    }

    let files = collect_files(&source_root)?;
    let total_bytes = files.iter().map(|entry| entry.size).sum::<u64>();

    let mut logs = Vec::new();
    logs.push(format!("workflow=windows-installer-usb"));
    logs.push(format!("target_disk={}", disk.id));
    logs.push(format!("target_mount={}", target_mount.display()));
    logs.push(format!("source_path={}", source_root.display()));
    logs.push(format!("file_count={}", files.len()));
    logs.push(format!("total_bytes={}", total_bytes));
    logs.push("partition_format=preformatted".to_string());

    let mut copied_files = 0usize;
    let mut copied_bytes = 0u64;

    if !params.dry_run {
        let ctx = SafetyContext {
            force_mode: params.force,
            confirmation_token: params.confirmation_token.clone(),
        };

        match can_write_to_disk(&ctx, disk.is_system_disk) {
            SafetyDecision::Allow => {}
            SafetyDecision::Deny(reason) => return Err(anyhow!(reason)),
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
        "copied_files": copied_files,
        "copied_bytes": copied_bytes,
        "dry_run": params.dry_run
    });

    let report = create_report_bundle_with_meta(
        &params.report_base,
        &graph,
        Some(meta),
        Some(&logs.join("\n")),
    )?;

    Ok(WindowsInstallerUsbResult {
        report,
        target_mount,
        copied_files,
        copied_bytes,
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
