use anyhow::{anyhow, Result};
use clap::{Parser, Subcommand};

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
        } => {
            #[cfg(windows)]
            {
                let hashes = phoenix_imaging::hash_disk_readonly_physicaldrive(
                    &disk,
                    size_bytes,
                    chunk_size,
                    max_chunks,
                )?;
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
    }
}
