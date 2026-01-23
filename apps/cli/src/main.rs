use anyhow::{anyhow, Result};
use clap::{Parser, Subcommand};
use phoenix_imaging::{HashProgress, ProgressObserver};
use phoenix_workflow_engine::{
    run_disk_hash_report, run_unix_installer_usb, run_windows_apply_image,
    run_windows_installer_usb, validate_workflow_definition, DiskHashReportParams,
    UnixInstallerUsbParams, WindowsApplyImageParams, WindowsInstallerUsbParams,
    run_stage_bootloader, BootloaderStageParams, run_macos_kext_stage, MacosKextStageParams,
};
use phoenix_host_windows::format::parse_filesystem;
use phoenix_content::{
    load_pack_manifest, load_workflow_definition, pack_signature_exists,
    resolve_pack_workflows, resolve_windows_image, sign_pack_manifest,
    verify_pack_manifest, PACK_SCHEMA_VERSION,
};
use phoenix_wim::{apply_image as wim_apply_image, list_images as wim_list_images};
use phoenix_core::{DeviceGraph, WorkflowDefinition};
use phoenix_legacy_patcher::{LegacyPatchParams, run_legacy_patch};

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

    /// Verify all report bundles under a root directory
    ReportVerifyTree {
        /// Root directory containing report subfolders
        #[arg(long)]
        root: String,

        /// Signing key hex for signature verification
        #[arg(long)]
        key: Option<String>,
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

    /// Create a Linux installer USB (copy-only, preformatted)
    LinuxInstallerUsb {
        /// Path to extracted Linux installer files
        #[arg(long)]
        source: String,

        /// Target mount path (preformatted)
        #[arg(long)]
        target_mount: String,

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

        /// Emit SHA-256 copy manifest into report
        #[arg(long)]
        hash_manifest: bool,

        /// Optional device path to format as FAT32 before staging
        #[arg(long)]
        format_device: Option<String>,

        /// Device size in bytes (required if format_device set)
        #[arg(long)]
        format_size_bytes: Option<u64>,

        /// Volume label for FAT32 formatting
        #[arg(long)]
        format_label: Option<String>,
    },

    /// Create a macOS installer USB (copy-only, preformatted)
    MacosInstallerUsb {
        /// Path to extracted macOS installer files
        #[arg(long)]
        source: String,

        /// Target mount path (preformatted)
        #[arg(long)]
        target_mount: String,

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

        /// Emit SHA-256 copy manifest into report
        #[arg(long)]
        hash_manifest: bool,

        /// Optional device path to format as FAT32 before staging
        #[arg(long)]
        format_device: Option<String>,

        /// Device size in bytes (required if format_device set)
        #[arg(long)]
        format_size_bytes: Option<u64>,

        /// Volume label for FAT32 formatting
        #[arg(long)]
        format_label: Option<String>,
    },

    /// Write a raw Linux image to a device (destructive)
    LinuxWriteImage {
        /// Source image file (iso/img)
        #[arg(long)]
        source: String,

        /// Target block device (e.g. /dev/sdb)
        #[arg(long)]
        device: String,

        /// Base path for reports (default: current directory)
        #[arg(long, default_value = ".")]
        report_base: String,

        /// Force destructive operations
        #[arg(long)]
        force: bool,

        /// Confirmation token (PHX-...)
        #[arg(long)]
        token: Option<String>,

        /// Execute write (omit for dry-run)
        #[arg(long)]
        execute: bool,

        /// Verify by hashing device after write
        #[arg(long)]
        verify: bool,

        /// Chunk size (default 8MB)
        #[arg(long, default_value_t = 8 * 1024 * 1024)]
        chunk_size: u64,
    },

    /// Write a raw macOS image to a device (destructive)
    MacosWriteImage {
        /// Source image file (iso/img)
        #[arg(long)]
        source: String,

        /// Target block device (e.g. /dev/disk2)
        #[arg(long)]
        device: String,

        /// Base path for reports (default: current directory)
        #[arg(long, default_value = ".")]
        report_base: String,

        /// Force destructive operations
        #[arg(long)]
        force: bool,

        /// Confirmation token (PHX-...)
        #[arg(long)]
        token: Option<String>,

        /// Execute write (omit for dry-run)
        #[arg(long)]
        execute: bool,

        /// Verify by hashing device after write
        #[arg(long)]
        verify: bool,

        /// Chunk size (default 8MB)
        #[arg(long, default_value_t = 8 * 1024 * 1024)]
        chunk_size: u64,
    },

    /// Prepare Linux boot files on target mount
    LinuxBootPrep {
        /// Path to source files
        #[arg(long)]
        source: String,

        /// Target mount path
        #[arg(long)]
        target_mount: String,

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

        /// Emit SHA-256 copy manifest into report
        #[arg(long)]
        hash_manifest: bool,
    },

    /// Prepare macOS boot files on target mount
    MacosBootPrep {
        /// Path to source files
        #[arg(long)]
        source: String,

        /// Target mount path
        #[arg(long)]
        target_mount: String,

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

        /// Emit SHA-256 copy manifest into report
        #[arg(long)]
        hash_manifest: bool,
    },

    /// Create a macOS installer USB (uses Apple tools)
    MacosCreateInstaller {
        /// Source path (Install macOS.app or .dmg)
        #[arg(long)]
        source: String,

        /// Target device (e.g. /dev/disk2)
        #[arg(long)]
        target_device: String,

        /// Volume name for createinstallmedia
        #[arg(long, default_value = "PHOENIX-MACOS")]
        volume_name: String,

        /// macOS version or codename (e.g. 10.6, snow leopard, tahoe)
        #[arg(long)]
        macos_version: Option<String>,

        /// Filesystem override (APFS or JHFS+)
        #[arg(long)]
        filesystem: Option<String>,

        /// Base path for reports (default: current directory)
        #[arg(long, default_value = ".")]
        report_base: String,

        /// Force destructive operations
        #[arg(long)]
        force: bool,

        /// Confirmation token (PHX-...)
        #[arg(long)]
        token: Option<String>,

        /// Execute creation (omit for dry-run)
        #[arg(long)]
        execute: bool,
    },

    /// Patch macOS installer for unsupported Macs (Legacy Patcher)
    MacosLegacyPatch {
        /// Source path (Install macOS.app or mounted DMG)
        #[arg(long)]
        source: String,

        /// Override model identifier
        #[arg(long)]
        model: Option<String>,

        /// Override board-id
        #[arg(long)]
        board_id: Option<String>,

        /// Base path for reports (default: current directory)
        #[arg(long, default_value = ".")]
        report_base: String,

        /// Force destructive operations
        #[arg(long)]
        force: bool,

        /// Confirmation token (PHX-...)
        #[arg(long)]
        token: Option<String>,

        /// Execute patch (omit for dry-run)
        #[arg(long)]
        execute: bool,
    },

    /// Stage a custom bootloader package onto a target mount
    StageBootloader {
        /// Bootloader package root (must include EFI/BOOT/*.EFI)
        #[arg(long)]
        source: String,

        /// Target mount path
        #[arg(long)]
        target_mount: String,

        /// Optional target subdirectory (default: root)
        #[arg(long)]
        target_subdir: Option<String>,

        /// Base path for reports (default: current directory)
        #[arg(long, default_value = ".")]
        report_base: String,

        /// Force destructive operations
        #[arg(long)]
        force: bool,

        /// Confirmation token (PHX-...)
        #[arg(long)]
        token: Option<String>,

        /// Execute staging (omit for dry-run)
        #[arg(long)]
        execute: bool,

        /// Emit SHA-256 copy manifest into report
        #[arg(long)]
        hash_manifest: bool,
    },

    /// Stage macOS kext bundles into EFI/OC/Kexts
    MacosKextStage {
        /// Source directory containing .kext bundles
        #[arg(long)]
        source: String,

        /// Target mount path
        #[arg(long)]
        target_mount: String,

        /// Optional target subdirectory (default: EFI/OC/Kexts)
        #[arg(long)]
        target_subdir: Option<String>,

        /// Base path for reports (default: current directory)
        #[arg(long, default_value = ".")]
        report_base: String,

        /// Force destructive operations
        #[arg(long)]
        force: bool,

        /// Confirmation token (PHX-...)
        #[arg(long)]
        token: Option<String>,

        /// Execute staging (omit for dry-run)
        #[arg(long)]
        execute: bool,

        /// Emit SHA-256 copy manifest into report
        #[arg(long)]
        hash_manifest: bool,
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

    /// Validate a workflow definition file
    WorkflowValidate {
        /// Path to workflow JSON/YAML file
        #[arg(long)]
        file: String,
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

        /// Optional signing key hex (verifies signature if present)
        #[arg(long)]
        key: Option<String>,
    },

    /// Run all workflows listed in a pack manifest
    PackRun {
        /// Path to pack manifest JSON
        #[arg(long)]
        manifest: String,

        /// Default report base for workflow runs
        #[arg(long, default_value = ".")]
        report_base: String,

        /// Require pack signature verification
        #[arg(long)]
        require_signed: bool,

        /// Signing key hex (overrides env PHOENIX_PACK_KEY)
        #[arg(long)]
        key: Option<String>,
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
            let graph = build_device_graph()?;
            if pretty {
                println!("{}", serde_json::to_string_pretty(&graph)?);
            } else {
                println!("{}", serde_json::to_string(&graph)?);
            }
            Ok(())
        }
        Commands::Report { base } => {
            let graph = build_device_graph()?;
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

        Commands::ReportVerify { path, key } => {
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

        Commands::ReportExport { path, out } => {
            let output = phoenix_report::export_report_zip(path, out)?;
            println!("exported: {}", output.display());
            Ok(())
        }

        Commands::ReportVerifyTree { root, key } => {
            let result = phoenix_report::verify_report_tree(root, key.as_deref())?;
            println!("total_reports: {}", result.total_reports);
            println!("ok_reports: {}", result.ok_reports);
            if !result.failed_reports.is_empty() {
                println!("failed_reports:");
                for report in &result.failed_reports {
                    println!("  - {}", report);
                }
            }
            if result.failed_reports.is_empty() {
                Ok(())
            } else {
                Err(anyhow!("one or more reports failed verification"))
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

        Commands::LinuxInstallerUsb {
            source,
            target_mount,
            report_base,
            force,
            token,
            execute,
            hash_manifest,
            format_device,
            format_size_bytes,
            format_label,
        } => {
            #[cfg(target_os = "linux")]
            {
                let params = UnixInstallerUsbParams {
                    source_path: source.into(),
                    target_mount: target_mount.into(),
                    report_base: report_base.into(),
                    force,
                    confirmation_token: token,
                    dry_run: !execute,
                    hash_manifest,
                    format_device: format_device.map(Into::into),
                    format_size_bytes,
                    format_label,
                };
                let result = run_unix_installer_usb(&params)?;
                println!("Linux USB staging complete:");
                println!("  dry_run: {}", result.dry_run);
                println!("  target_mount: {}", result.target_mount.display());
                println!("  copied_files: {}", result.copied_files);
                println!("  copied_bytes: {}", result.copied_bytes);
                println!("  report_root: {}", result.report.root.display());
                Ok(())
            }
            #[cfg(not(target_os = "linux"))]
            {
                Err(anyhow!("linux-only command"))
            }
        }

        Commands::MacosInstallerUsb {
            source,
            target_mount,
            report_base,
            force,
            token,
            execute,
            hash_manifest,
            format_device,
            format_size_bytes,
            format_label,
        } => {
            #[cfg(target_os = "macos")]
            {
                let params = UnixInstallerUsbParams {
                    source_path: source.into(),
                    target_mount: target_mount.into(),
                    report_base: report_base.into(),
                    force,
                    confirmation_token: token,
                    dry_run: !execute,
                    hash_manifest,
                    format_device: format_device.map(Into::into),
                    format_size_bytes,
                    format_label,
                };
                let result = run_unix_installer_usb(&params)?;
                println!("macOS USB staging complete:");
                println!("  dry_run: {}", result.dry_run);
                println!("  target_mount: {}", result.target_mount.display());
                println!("  copied_files: {}", result.copied_files);
                println!("  copied_bytes: {}", result.copied_bytes);
                println!("  report_root: {}", result.report.root.display());
                Ok(())
            }
            #[cfg(not(target_os = "macos"))]
            {
                Err(anyhow!("macos-only command"))
            }
        }

        Commands::LinuxWriteImage {
            source,
            device,
            report_base,
            force,
            token,
            execute,
            verify,
            chunk_size,
        } => {
            #[cfg(target_os = "linux")]
            {
                let params = phoenix_workflow_engine::UnixWriteImageParams {
                    source_image: source.into(),
                    target_device: device.into(),
                    report_base: report_base.into(),
                    force,
                    confirmation_token: token,
                    dry_run: !execute,
                    verify,
                    chunk_size,
                };
                let result = phoenix_workflow_engine::run_unix_write_image(&params)?;
                println!("Linux image write complete:");
                println!("  dry_run: {}", result.dry_run);
                println!("  bytes_written: {}", result.bytes_written);
                println!("  sha256: {}", result.sha256);
                println!("  verify_ok: {:?}", result.verify_ok);
                println!("  report_root: {}", result.report.root.display());
                Ok(())
            }
            #[cfg(not(target_os = "linux"))]
            {
                Err(anyhow!("linux-only command"))
            }
        }

        Commands::MacosWriteImage {
            source,
            device,
            report_base,
            force,
            token,
            execute,
            verify,
            chunk_size,
        } => {
            #[cfg(target_os = "macos")]
            {
                let params = phoenix_workflow_engine::UnixWriteImageParams {
                    source_image: source.into(),
                    target_device: device.into(),
                    report_base: report_base.into(),
                    force,
                    confirmation_token: token,
                    dry_run: !execute,
                    verify,
                    chunk_size,
                };
                let result = phoenix_workflow_engine::run_unix_write_image(&params)?;
                println!("macOS image write complete:");
                println!("  dry_run: {}", result.dry_run);
                println!("  bytes_written: {}", result.bytes_written);
                println!("  sha256: {}", result.sha256);
                println!("  verify_ok: {:?}", result.verify_ok);
                println!("  report_root: {}", result.report.root.display());
                Ok(())
            }
            #[cfg(not(target_os = "macos"))]
            {
                Err(anyhow!("macos-only command"))
            }
        }

        Commands::LinuxBootPrep {
            source,
            target_mount,
            report_base,
            force,
            token,
            execute,
            hash_manifest,
        } => {
            #[cfg(target_os = "linux")]
            {
                let params = phoenix_workflow_engine::UnixBootPrepParams {
                    source_path: source.into(),
                    target_mount: target_mount.into(),
                    report_base: report_base.into(),
                    force,
                    confirmation_token: token,
                    dry_run: !execute,
                    hash_manifest,
                };
                let result = phoenix_workflow_engine::run_unix_boot_prep(&params)?;
                println!("Linux boot prep complete:");
                println!("  dry_run: {}", result.dry_run);
                println!("  copied_files: {}", result.copied_files);
                println!("  copied_bytes: {}", result.copied_bytes);
                println!("  report_root: {}", result.report.root.display());
                Ok(())
            }
            #[cfg(not(target_os = "linux"))]
            {
                Err(anyhow!("linux-only command"))
            }
        }

        Commands::MacosBootPrep {
            source,
            target_mount,
            report_base,
            force,
            token,
            execute,
            hash_manifest,
        } => {
            #[cfg(target_os = "macos")]
            {
                let params = phoenix_workflow_engine::UnixBootPrepParams {
                    source_path: source.into(),
                    target_mount: target_mount.into(),
                    report_base: report_base.into(),
                    force,
                    confirmation_token: token,
                    dry_run: !execute,
                    hash_manifest,
                };
                let result = phoenix_workflow_engine::run_unix_boot_prep(&params)?;
                println!("macOS boot prep complete:");
                println!("  dry_run: {}", result.dry_run);
                println!("  copied_files: {}", result.copied_files);
                println!("  copied_bytes: {}", result.copied_bytes);
                println!("  report_root: {}", result.report.root.display());
                Ok(())
            }
            #[cfg(not(target_os = "macos"))]
            {
                Err(anyhow!("macos-only command"))
            }
        }

        Commands::MacosCreateInstaller {
            source,
            target_device,
            volume_name,
            macos_version,
            filesystem,
            report_base,
            force,
            token,
            execute,
        } => {
            #[cfg(target_os = "macos")]
            {
                let params = phoenix_workflow_engine::MacosInstallerUsbParams {
                    source_path: source.into(),
                    target_device: target_device.into(),
                    report_base: report_base.into(),
                    volume_name,
                    macos_version,
                    filesystem,
                    force,
                    confirmation_token: token,
                    dry_run: !execute,
                };
                let result = phoenix_workflow_engine::run_macos_installer_usb(&params)?;
                println!("macOS installer complete:");
                println!("  dry_run: {}", result.dry_run);
                println!("  mode: {}", result.mode);
                println!("  target_volume: {}", result.target_volume.display());
                println!("  report_root: {}", result.report.root.display());
                Ok(())
            }
            #[cfg(not(target_os = "macos"))]
            {
                Err(anyhow!("macos-only command"))
            }
        }

        Commands::MacosLegacyPatch {
            source,
            model,
            board_id,
            report_base,
            force,
            token,
            execute,
        } => {
            let params = LegacyPatchParams {
                source_path: source.into(),
                report_base: report_base.into(),
                model,
                board_id,
                force,
                confirmation_token: token,
                dry_run: !execute,
            };
            let result = run_legacy_patch(&params)?;
            println!("Legacy patch complete:");
            println!("  dry_run: {}", result.dry_run);
            println!("  patched_files: {}", result.patched_files.len());
            for file in &result.patched_files {
                println!("  patched: {}", file);
            }
            println!("  report_root: {}", result.report.root.display());
            Ok(())
        }

        Commands::StageBootloader {
            source,
            target_mount,
            target_subdir,
            report_base,
            force,
            token,
            execute,
            hash_manifest,
        } => {
            let params = BootloaderStageParams {
                source_path: source.into(),
                target_mount: target_mount.into(),
                target_subdir: target_subdir.map(Into::into),
                report_base: report_base.into(),
                force,
                confirmation_token: token,
                dry_run: !execute,
                hash_manifest,
            };
            let result = run_stage_bootloader(&params)?;
            println!("Bootloader staging complete:");
            println!("  dry_run: {}", result.dry_run);
            println!("  copied_files: {}", result.copied_files);
            println!("  copied_bytes: {}", result.copied_bytes);
            println!("  report_root: {}", result.report.root.display());
            Ok(())
        }

        Commands::MacosKextStage {
            source,
            target_mount,
            target_subdir,
            report_base,
            force,
            token,
            execute,
            hash_manifest,
        } => {
            #[cfg(target_os = "macos")]
            {
                let params = MacosKextStageParams {
                    source_path: source.into(),
                    target_mount: target_mount.into(),
                    target_subdir: target_subdir.map(Into::into),
                    report_base: report_base.into(),
                    force,
                    confirmation_token: token,
                    dry_run: !execute,
                    hash_manifest,
                };
                let result = run_macos_kext_stage(&params)?;
                println!("macOS kext staging complete:");
                println!("  dry_run: {}", result.dry_run);
                println!("  copied_files: {}", result.copied_files);
                println!("  copied_bytes: {}", result.copied_bytes);
                println!("  report_root: {}", result.report.root.display());
                Ok(())
            }
            #[cfg(not(target_os = "macos"))]
            {
                Err(anyhow!("macos-only command"))
            }
        }

        Commands::WorkflowRun { file, report_base } => {
            let definition: WorkflowDefinition = load_workflow_definition(&file)?;
            validate_workflow_definition(&definition)?;
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

        Commands::WorkflowValidate { file } => {
            let definition: WorkflowDefinition = load_workflow_definition(&file)?;
            validate_workflow_definition(&definition)?;
            println!("workflow valid: {}", definition.name);
            Ok(())
        }

        Commands::DiskHashReport {
            disk,
            chunk_size,
            max_chunks,
            report_base,
        } => {
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

        Commands::PackValidate { manifest, key } => {
            let manifest_path = manifest;
            let manifest_data = load_pack_manifest(&manifest_path)?;
            println!("schema: {}", PACK_SCHEMA_VERSION);
            println!("pack: {} {}", manifest_data.name, manifest_data.version);
            if let Some(desc) = manifest_data.description {
                println!("description: {}", desc);
            }
            let workflows = resolve_pack_workflows(&manifest_path)?;
            println!("workflows: {}", workflows.len());
            for (path, workflow) in workflows {
                println!("  {} ({})", workflow.name, path.display());
            }
            let sig_present = pack_signature_exists(&manifest_path);
            println!("signature_present: {}", sig_present);
            if let Some(key) = resolve_pack_key(key) {
                if sig_present {
                    let ok = verify_pack_manifest(&manifest_path, &key)?;
                    println!("signature_valid: {}", ok);
                } else {
                    println!("signature_valid: false");
                }
            }
            Ok(())
        }

        Commands::PackRun {
            manifest,
            report_base,
            require_signed,
            key,
        } => {
            let manifest_data = load_pack_manifest(&manifest)?;
            println!("pack: {} {}", manifest_data.name, manifest_data.version);
            if require_signed {
                let sig_present = pack_signature_exists(&manifest);
                if !sig_present {
                    return Err(anyhow!("pack signature missing"));
                }
                let key = resolve_pack_key(key)
                    .ok_or_else(|| anyhow!("pack key required for signature verification"))?;
                let ok = verify_pack_manifest(&manifest, &key)?;
                if !ok {
                    return Err(anyhow!("pack signature invalid"));
                }
            }
            let workflows = resolve_pack_workflows(&manifest)?;
            let mut workflow_reports = Vec::new();
            for (path, workflow) in workflows {
                println!("running workflow: {} ({})", workflow.name, path.display());
                let result = phoenix_workflow_engine::run_workflow_definition_with_report(
                    &workflow,
                    report_base.clone().into(),
                )?;
                println!("  report: {}", result.report.root.display());
                workflow_reports.push(serde_json::json!({
                    "workflow": workflow.name,
                    "report_root": result.report.root.display().to_string()
                }));
            }
            let graph = build_device_graph()?;
            let key = std::env::var("PHOENIX_SIGNING_KEY").ok();
            let meta = serde_json::json!({
                "pack": {
                    "name": manifest_data.name,
                    "version": manifest_data.version
                },
                "workflow_reports": workflow_reports
            });
            let pack_report = phoenix_report::create_report_bundle_with_meta_and_signing(
                report_base,
                &graph,
                Some(meta),
                None,
                key.as_deref(),
            )?;
            println!("pack_report: {}", pack_report.root.display());
            Ok(())
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

fn resolve_pack_key(key: Option<String>) -> Option<String> {
    if let Some(key) = key {
        return Some(key);
    }
    std::env::var("PHOENIX_PACK_KEY").ok()
}
