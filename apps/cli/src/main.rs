use anyhow::{anyhow, Result};
use clap::{Parser, Subcommand};
use phoenix_imaging::{HashProgress, ProgressObserver};
use phoenix_workflow_engine::{run_windows_installer_usb, WindowsInstallerUsbParams};
use phoenix_host_windows::format::parse_filesystem;

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
                let paths = phoenix_report::create_report_bundle(base, &graph)?;
                println!("Report created:");
                println!("  run_id: {}", paths.run_id);
                println!("  root:   {}", paths.root.display());
                println!("  device_graph: {}", paths.device_graph_json.display());
                println!("  run.json:     {}", paths.run_json.display());
                println!("  logs:         {}", paths.logs_path.display());
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
                };
                let result = run_windows_installer_usb(&params)?;
                println!("Workflow complete:");
                println!("  dry_run: {}", result.dry_run);
                println!("  target_mount: {}", result.target_mount.display());
                println!("  copied_files: {}", result.copied_files);
                println!("  copied_bytes: {}", result.copied_bytes);
                println!("  report_root: {}", result.report.root.display());
                println!("  logs: {}", result.report.logs_path.display());
                Ok(())
            }
            #[cfg(not(windows))]
            {
                Err(anyhow!("Windows-first in M0"))
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
