use anyhow::{anyhow, Result};
use clap::{Parser, Subcommand};
use phoenix_imaging::{HashProgress, ProgressObserver};
use phoenix_workflow_engine::{
    run_disk_hash_report, run_windows_apply_image, run_windows_installer_usb,
    DiskHashReportParams, WindowsApplyImageParams, WindowsInstallerUsbParams,
};
use phoenix_host_windows::format::parse_filesystem;
use phoenix_content::{
    load_pack_manifest, load_workflow_definition, resolve_pack_workflows,
    resolve_windows_image, sign_pack_manifest, verify_pack_manifest,
};
use phoenix_wim::{apply_image as wim_apply_image, list_images as wim_list_images};
use phoenix_core::WorkflowDefinition;

#[derive(Parser)]
#[command(name = "phoenix-cli", version, about = "Phoenix Core CLI (Windows-first)")]
struct Cli {
    #[command(subcommand)]
    cmd: Commands,
}

#[derive(Subcommand)]
enum Commands {
    /// Print device graph JSON
    DeviceGraph {
        /// Pretty JSON output
        #[arg(long)]
        pretty: bool,
    },

    /// Create a report bundle (reports/<run_id>/)
    Report {
        /// Base path (default: current directory)
        #[arg(long, default_value = ".")]
        base: String,
    },

    /// Verify a report bundle (manifest + optional signature)
    ReportVerify {
        /// Path to reports/<run_id> directory
        #[arg(long)]
        path: String,

        /// Signing key hex for signature verification
        #[arg(long)]
        key: Option<String>,
    },

    /// Export a report bundle as zip
    ReportExport {
        /// Path to reports/<run_id> directory
        #[arg(long)]
        path: String,

        /// Output zip file path
        #[arg(long)]
        out: String,
    },

    /// Read-only hash chunks from a PhysicalDrive (Windows)
    HashDisk {
        /// Disk id like: PhysicalDrive0
        #[arg(long)]
        disk: String,

        /// Total size in bytes (use value from device graph disk.size_bytes)
        #[arg(long)]
        size_bytes: u64,

        /// Chunk size in bytes (default: 8MB)
        #[arg(long, default_value_t = 8 * 1024 * 1024)]
        chunk_size: u64,

        /// Max chunks to hash (safety for quick runs)
        #[arg(long)]
        max_chunks: Option<u64>,

        /// Print progress per chunk
        #[arg(long)]
        progress: bool,
    },

    /// Create a Windows installer USB (MVP)
    WindowsInstallerUsb {
        /// Disk id like: PhysicalDrive1
        #[arg(long)]
        disk: String,

        /// Path to extracted Windows installer files (directory)
        #[arg(long)]
        source: String,

        /// Optional target mount path override (e.g. E:\)
        #[arg(long)]
        mount: Option<String>,

        /// Base path for reports (default: current directory)
        #[arg(long, default_value = ".")]
        report_base: String,

        /// Force destructive operations
        #[arg(long)]
        force: bool,

        /// Confirmation token (PHX-...)
        #[arg(long)]
        token: Option<String>,

        /// Execute copy (omit for dry-run)
        #[arg(long)]
        execute: bool,

        /// Repartition disk (single GPT partition)
        #[arg(long)]
        repartition: bool,

        /// Format existing volume before staging
        #[arg(long)]
        format: bool,

        /// Filesystem for formatting (fat32|ntfs|exfat)
        #[arg(long, default_value = "fat32")]
        fs: String,

        /// Volume label for formatting
        #[arg(long)]
        label: Option<String>,

        /// Driver source directory to stage into $OEM$
        #[arg(long)]
        drivers: Option<String>,

        /// Driver target subdirectory (relative to USB root)
        #[arg(long)]
        drivers_target: Option<String>,

        /// Emit SHA-256 copy manifest into report
        #[arg(long)]
        hash_manifest: bool,
    },

    /// List images in a WIM/ESD file
    WimInfo {
        /// Path to .wim or .esd file
        #[arg(long)]
        path: String,
    },

    /// Apply a WIM/ESD image to a target directory
    WimApply {
        /// Path to .wim or .esd file
        #[arg(long)]
        path: String,

        /// Image index (1-based)
        #[arg(long)]
        index: u32,

        /// Target directory (must exist)
        #[arg(long)]
        target: String,
    },

    /// Apply a Windows image with reports + safety gates
    WindowsApplyImage {
        /// ISO, directory, or WIM/ESD path
        #[arg(long)]
        source: String,

        /// Image index (1-based)
        #[arg(long)]
        index: u32,

        /// Target directory (will be created)
        #[arg(long)]
        target: String,

        /// Base path for reports (default: current directory)
        #[arg(long, default_value = ".")]
        report_base: String,

        /// Force destructive operations
        #[arg(long)]
        force: bool,

        /// Confirmation token (PHX-...)
        #[arg(long)]
        token: Option<String>,

        /// Execute apply (omit for dry-run)
        #[arg(long)]
        execute: bool,

        /// Verify byte totals after apply
        #[arg(long)]
        verify: bool,
    },

    /// Run a workflow definition JSON file
    WorkflowRun {
        /// Path to workflow JSON file
        #[arg(long)]
        file: String,

        /// Default report base for steps without report_base
        #[arg(long, default_value = ".")]
        report_base: String,
    },

    /// Hash a disk and emit a report bundle
    DiskHashReport {
        /// Disk id like: PhysicalDrive0
        #[arg(long)]
        disk: String,

        /// Chunk size in bytes (default: 8MB)
        #[arg(long, default_value_t = 8 * 1024 * 1024)]
        chunk_size: u64,

        /// Max chunks to hash
        #[arg(long)]
        max_chunks: Option<u64>,

        /// Base path for reports (default: current directory)
        #[arg(long, default_value = ".")]
        report_base: String,
    },

    /// Validate a Phoenix pack manifest and workflows
    PackValidate {
        /// Path to pack manifest JSON
        #[arg(long)]
        manifest: String,
    },

    /// Run all workflows listed in a pack manifest
    PackRun {
        /// Path to pack manifest JSON
        #[arg(long)]
        manifest: String,

        /// Default report base for workflow runs
        #[arg(long, default_value = ".")]
        report_base: String,
    },

    /// Sign a pack manifest (writes .sig)
    PackSign {
        /// Path to pack manifest JSON/YAML
        #[arg(long)]
        manifest: String,

        /// Signing key hex
        #[arg(long)]
        key: String,
    },

    /// Verify a pack manifest signature
    PackVerify {
        /// Path to pack manifest JSON/YAML
        #[arg(long)]
        manifest: String,

        /// Signing key hex
        #[arg(long)]
        key: String,
    },
}

fn main() -> Result<()> {
    let cli = Cli::parse();

    match cli.cmd {
        Commands::DeviceGraph { pretty } => {
            #[cfg(windows)]
            {
                let graph = phoenix_host_windows::build_device_graph()?;
                if pretty {
                    println!("{}", serde_json::to_string_pretty(&graph)?);
                } else {
                    println!("{}", serde_json::to_string(&graph)?);
                }
                Ok(())
            }
            #[cfg(not(windows))]
            {
                Err(anyhow!("Windows-first in M0"))
            }
        }
        Commands::Report { base } => {
            #[cfg(windows)]
            {
                let graph = phoenix_host_windows::build_device_graph()?;
                let key = std::env::var("PHOENIX_SIGNING_KEY").ok();
                let paths = phoenix_report::create_report_bundle_with_meta_and_signing(
                    base,
                    &graph,
                    None,
                    None,
                    key.as_deref(),
                )?;
                println!("Report created:");
                println!("  run_id: {}", paths.run_id);
                println!("  root:   {}", paths.root.display());
                println!("  device_graph: {}", paths.device_graph_json.display());
                println!("  run.json:     {}", paths.run_json.display());
                println!("  logs:         {}", paths.logs_path.display());
                println!("  manifest:     {}", paths.manifest_path.display());
                if let Some(sig) = paths.signature_path.as_ref() {
                    println!("  signature:    {}", sig.display());
                }
                Ok(())
            }
            #[cfg(not(windows))]
            {
                Err(anyhow!("Windows-first in M0"))
            }
        }

        Commands::ReportVerify { path, key } => {
            #[cfg(windows)]
            {
                let result = phoenix_report::verify_report_bundle(path, key.as_deref())?;
                println!("verified_entries: {}", result.entries_checked);
                println!("signature_valid: {:?}", result.signature_valid);
                if !result.mismatches.is_empty() {
                    println!("mismatches:");
                    for mismatch in &result.mismatches {
                        println!("  - {}", mismatch);
                    }
                }
                if result.ok {
                    Ok(())
                } else {
                    Err(anyhow!("report verification failed"))
                }
            }
            #[cfg(not(windows))]
            {
                Err(anyhow!("Windows-first in M0"))
            }
        }

        Commands::ReportExport { path, out } => {
            #[cfg(windows)]
            {
                let output = phoenix_report::export_report_zip(path, out)?;
                println!("exported: {}", output.display());
                Ok(())
            }
            #[cfg(not(windows))]
            {
                Err(anyhow!("Windows-first in M0"))
            }
        }
        Commands::HashDisk {
            disk,
            size_bytes,
            chunk_size,
            max_chunks,
            progress,
        } => {
            #[cfg(windows)]
            {
                let hashes = if progress {
                    let mut observer = CliProgress::new();
                    phoenix_imaging::hash_disk_readonly_physicaldrive_with_progress(
                        &disk,
                        size_bytes,
                        chunk_size,
                        max_chunks,
                        &mut observer,
                    )?
                } else {
                    phoenix_imaging::hash_disk_readonly_physicaldrive(
                        &disk,
                        size_bytes,
                        chunk_size,
                        max_chunks,
                    )?
                };
                for (index, hash) in hashes {
                    println!("chunk {}: {}", index, hash);
                }
                Ok(())
            }
            #[cfg(not(windows))]
            {
                Err(anyhow!("Windows-first in M0"))
            }
        }

        Commands::WindowsInstallerUsb {
            disk,
            source,
            mount,
            report_base,
            force,
            token,
            execute,
            repartition,
            format,
            fs,
            label,
            drivers,
            drivers_target,
            hash_manifest,
        } => {
            #[cfg(windows)]
            {
                let filesystem = parse_filesystem(&fs)
                    .ok_or_else(|| anyhow!("unsupported filesystem: {}", fs))?;
                let params = WindowsInstallerUsbParams {
                    target_disk_id: disk,
                    source_path: source.into(),
                    target_mount: mount.map(Into::into),
                    report_base: report_base.into(),
                    force,
                    confirmation_token: token,
                    dry_run: !execute,
                    repartition,
                    format,
                    filesystem,
                    label,
                    driver_source: drivers.map(Into::into),
                    driver_target: drivers_target.map(Into::into),
                    hash_manifest,
                };
                let result = run_windows_installer_usb(&params)?;
                println!("Workflow complete:");
                println!("  dry_run: {}", result.dry_run);
                println!("  target_mount: {}", result.target_mount.display());
                println!("  copied_files: {}", result.copied_files);
                println!("  copied_bytes: {}", result.copied_bytes);
                println!("  driver_files: {}", result.driver_files);
                println!("  driver_bytes: {}", result.driver_bytes);
                println!("  report_root: {}", result.report.root.display());
                println!("  logs: {}", result.report.logs_path.display());
                println!("  manifest: {}", result.report.manifest_path.display());
                if let Some(sig) = result.report.signature_path.as_ref() {
                    println!("  signature: {}", sig.display());
                }
                Ok(())
            }
            #[cfg(not(windows))]
            {
                Err(anyhow!("Windows-first in M0"))
            }
        }

        Commands::WimInfo { path } => {
            #[cfg(windows)]
            {
                let (image_path, _prepared) = resolve_windows_image(path)?;
                let images = wim_list_images(image_path)?;
                for image in images {
                    println!("Image {}", image.index);
                    if let Some(name) = image.name {
                        println!("  name: {}", name);
                    }
                    if let Some(desc) = image.description {
                        println!("  description: {}", desc);
                    }
                    if let Some(bytes) = image.total_bytes {
                        println!("  total_bytes: {}", bytes);
                    }
                }
                Ok(())
            }
            #[cfg(not(windows))]
            {
                Err(anyhow!("Windows-first in M0"))
            }
        }

        Commands::WimApply { path, index, target } => {
            #[cfg(windows)]
            {
                let (image_path, _prepared) = resolve_windows_image(path)?;
                wim_apply_image(image_path, index, target)?;
                println!("WIM apply complete.");
                Ok(())
            }
            #[cfg(not(windows))]
            {
                Err(anyhow!("Windows-first in M0"))
            }
        }

        Commands::WindowsApplyImage {
            source,
            index,
            target,
            report_base,
            force,
            token,
            execute,
            verify,
        } => {
            #[cfg(windows)]
            {
                let params = WindowsApplyImageParams {
                    source_path: source.into(),
                    image_index: index,
                    target_dir: target.into(),
                    report_base: report_base.into(),
                    force,
                    confirmation_token: token,
                    dry_run: !execute,
                    verify,
                };
                let result = run_windows_apply_image(&params)?;
                println!("Apply complete:");
                println!("  dry_run: {}", result.dry_run);
                println!("  target_dir: {}", result.target_dir.display());
                println!("  file_count: {}", result.file_count);
                println!("  total_bytes: {}", result.total_bytes);
                println!("  report_root: {}", result.report.root.display());
                println!("  manifest: {}", result.report.manifest_path.display());
                if let Some(sig) = result.report.signature_path.as_ref() {
                    println!("  signature: {}", sig.display());
                }
                Ok(())
            }
            #[cfg(not(windows))]
            {
                Err(anyhow!("Windows-first in M0"))
            }
        }

        Commands::WorkflowRun { file, report_base } => {
            #[cfg(windows)]
            {
                let definition: WorkflowDefinition = load_workflow_definition(&file)?;
                let result = phoenix_workflow_engine::run_workflow_definition_with_report(
                    &definition,
                    report_base.into(),
                )?;
                println!("workflow: {}", definition.name);
                for step in &result.steps {
                    println!(
                        "step {}: {} ({} ms)",
                        step.id, step.action, step.duration_ms
                    );
                    if let Some(root) = step.report_root {
                        println!("  report: {}", root.display());
                    }
                }
                println!("workflow_report: {}", result.report.root.display());
                Ok(())
            }
            #[cfg(not(windows))]
            {
                Err(anyhow!("Windows-first in M0"))
            }
        }

        Commands::DiskHashReport {
            disk,
            chunk_size,
            max_chunks,
            report_base,
        } => {
            #[cfg(windows)]
            {
                let params = DiskHashReportParams {
                    disk_id: disk,
                    chunk_size,
                    max_chunks,
                    report_base: report_base.into(),
                };
                let result = run_disk_hash_report(&params)?;
                println!("Disk hash report:");
                println!("  disk_id: {}", result.disk_id);
                println!("  chunk_count: {}", result.chunk_count);
                println!("  report_root: {}", result.report.root.display());
                println!("  manifest: {}", result.report.manifest_path.display());
                if let Some(sig) = result.report.signature_path.as_ref() {
                    println!("  signature: {}", sig.display());
                }
                Ok(())
            }
            #[cfg(not(windows))]
            {
                Err(anyhow!("Windows-first in M0"))
            }
        }

        Commands::PackValidate { manifest } => {
            let manifest_path = manifest;
            let manifest_data = load_pack_manifest(&manifest_path)?;
            println!("pack: {} {}", manifest_data.name, manifest_data.version);
            if let Some(desc) = manifest_data.description {
                println!("description: {}", desc);
            }
            let workflows = resolve_pack_workflows(&manifest_path)?;
            println!("workflows: {}", workflows.len());
            for (path, workflow) in workflows {
                println!("  {} ({})", workflow.name, path.display());
            }
            Ok(())
        }

        Commands::PackRun {
            manifest,
            report_base,
        } => {
            #[cfg(windows)]
            {
                let manifest_data = load_pack_manifest(&manifest)?;
                println!("pack: {} {}", manifest_data.name, manifest_data.version);
                let workflows = resolve_pack_workflows(&manifest)?;
                for (path, workflow) in workflows {
                    println!("running workflow: {} ({})", workflow.name, path.display());
                    let result = phoenix_workflow_engine::run_workflow_definition_with_report(
                        &workflow,
                        report_base.clone().into(),
                    )?;
                    println!("  report: {}", result.report.root.display());
                }
                Ok(())
            }
            #[cfg(not(windows))]
            {
                Err(anyhow!("Windows-first in M0"))
            }
        }

        Commands::PackSign { manifest, key } => {
            let sig_path = sign_pack_manifest(&manifest, &key)?;
            println!("signature: {}", sig_path.display());
            Ok(())
        }

        Commands::PackVerify { manifest, key } => {
            let ok = verify_pack_manifest(&manifest, &key)?;
            if ok {
                println!("pack signature valid");
                Ok(())
            } else {
                Err(anyhow!("pack signature invalid"))
            }
        }
    }
}

struct CliProgress {
    last_percent: u64,
}

impl CliProgress {
    fn new() -> Self {
        Self { last_percent: 0 }
    }
}

impl ProgressObserver for CliProgress {
    fn on_progress(&mut self, progress: HashProgress) -> bool {
        if progress.total_bytes == 0 {
            return true;
        }
        let percent = (progress.bytes_hashed * 100) / progress.total_bytes;
        if percent >= self.last_percent + 5 || percent == 100 {
            println!(
                "progress: {}% (chunk {}/{})",
                percent, progress.chunk_index + 1, progress.total_chunks
            );
            self.last_percent = percent;
        }
        true
    }
}
