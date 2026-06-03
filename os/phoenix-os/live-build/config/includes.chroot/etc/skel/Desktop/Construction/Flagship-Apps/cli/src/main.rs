use anyhow::Context;
use clap::{Parser, Subcommand};
use phoenix_core::{DeviceGraph, RunReport};
use phoenix_host_windows::build_device_graph;
use std::fs;
use std::path::PathBuf;

#[derive(Parser)]
#[command(name = "phoenix-cli")]
#[command(about = "Phoenix Core CLI", long_about = None)]
struct Cli {
    #[command(subcommand)]
    command: Commands,
}

#[derive(Subcommand)]
enum Commands {
    /// Generate and display the device graph
    DeviceGraph {
        /// Output in JSON format
        #[arg(long)]
        json: bool,
        /// Pretty print JSON
        #[arg(long)]
        pretty: bool,
    },
    /// Create a report bundle
    Report {
        /// Base path for the report bundle
        #[arg(long, default_value = ".")]
        base: PathBuf,
    },
    /// Hash a disk in chunks (read-only)
    HashDisk {
        /// Disk identifier (e.g. PhysicalDrive1)
        #[arg(long)]
        disk: String,
        /// Total size in bytes to read
        #[arg(long)]
        size_bytes: u64,
        /// Chunk size in bytes (default 8MB)
        #[arg(long, default_value_t = 8 * 1024 * 1024)]
        chunk_bytes: usize,
        /// Maximum number of chunks to process
        #[arg(long)]
        max_chunks: Option<usize>,
        /// Save hashes to report bundle
        #[arg(long)]
        report: bool,
    },
    /// Generate a safety confirmation token
    RequestToken,
    /// Run a safety preflight check on a disk
    Preflight {
        /// Disk identifier
        #[arg(long)]
        disk: String,
        /// Force mode
        #[arg(long)]
        force: bool,
        /// Confirmation token
        #[arg(long)]
        token: Option<String>,
    },
    /// Run a transactional job with JSON progress streaming
    RunJob {
        /// JSON job payload
        #[arg(long)]
        json: String,
    },
}

fn main() -> anyhow::Result<()> {
    let cli = Cli::parse();

    match cli.command {
        Commands::RunJob { json } => {
            use phoenix_core::orchestrator::Orchestrator;
            let orch = Orchestrator::new();
            orch.execute_job(&json)?;
        }
        Commands::DeviceGraph { json, pretty } => {
            let graph = build_device_graph()?;
            if json {
                println!("{}", graph.to_json(pretty)?);
            } else {
                println!("Device Graph Generated (ID: {})", graph.run_id);
                println!(
                    "Host: {} ({})",
                    graph.host_info.hostname, graph.host_info.os
                );
                println!("Disks found: {}", graph.disks.len());
            }
        }
        Commands::Report { base } => {
            generate_report(base, None)?;
        }
        Commands::HashDisk {
            disk,
            size_bytes,
            chunk_bytes,
            max_chunks,
            report,
        } => {
            use phoenix_imaging::{hash_disk_chunks, ChunkPlan};

            let plan = ChunkPlan::new(size_bytes, chunk_bytes);
            println!(
                "Starting read-only hash of {} ({} chunks)",
                disk, plan.total_chunks
            );

            let hashes = hash_disk_chunks(&disk, &plan, max_chunks)?;

            if report {
                let report_dir = generate_report(PathBuf::from("."), Some(&hashes))?;
                println!("Hashes written to: {:?}", report_dir.join("hashes.json"));
            } else {
                for h in hashes.iter().take(5) {
                    println!("Chunk {}: {}", h.index, h.hash);
                }
                if hashes.len() > 5 {
                    println!("... and {} more", hashes.len() - 5);
                }
            }
        }
        Commands::RequestToken => {
            use phoenix_safety::require_confirmation_token;
            let token = require_confirmation_token();
            println!("SAFETY TOKEN GENERATED: {}", token);
            println!("Use this token with --token to authorize destructive operations.");
        }
        Commands::Preflight { disk, force, token } => {
            use phoenix_safety::{can_write_to_disk, SafetyContext, SafetyDecision};

            // First, find the disk in the device graph to see if it's a system disk
            let graph = build_device_graph()?;
            let disk_info = graph.disks.iter().find(|d| d.id == disk);

            let is_system = disk_info.map(|d| d.is_system_disk).unwrap_or(false);

            let ctx = SafetyContext {
                force_mode: force,
                confirmation_token: token,
            };

            match can_write_to_disk(&ctx, is_system) {
                SafetyDecision::Allow => {
                    println!(
                        "SUCCESS: Preflight passed for {}. Operation is AUTHORIZED.",
                        disk
                    );
                }
                SafetyDecision::Deny(reason) => {
                    println!("DENIED: Safety policy violation!");
                    println!("Reason: {}", reason);
                    return Err(anyhow::anyhow!("Safety preflight failed."));
                }
            }
        }
    }

    Ok(())
}

fn generate_report(
    base: PathBuf,
    hashes: Option<&Vec<phoenix_imaging::ChunkHash>>,
) -> anyhow::Result<PathBuf> {
    let graph = build_device_graph()?;
    let run_id = graph.run_id.to_string();
    let report_dir = base.join("reports").join(&run_id);

    fs::create_dir_all(&report_dir)
        .with_context(|| format!("Failed to create report directory: {:?}", report_dir))?;

    // 1. device_graph.json
    let graph_json = graph.to_json(true)?;
    fs::write(report_dir.join("device_graph.json"), graph_json)?;

    // 2. run.json
    let run_report = RunReport {
        run_id: graph.run_id,
        timestamp: graph.timestamp,
        status: "SUCCESS".to_string(),
        message: "Phoenix Core report generated.".to_string(),
    };
    fs::write(
        report_dir.join("run.json"),
        serde_json::to_string_pretty(&run_report)?,
    )?;

    // 3. log.txt
    let log_content = format!(
        "Phoenix Core Run Log\nRun ID: {}\nTimestamp: {}\nHost: {}\nStatus: SUCCESS\n",
        graph.run_id, graph.timestamp, graph.host_info.hostname
    );
    fs::write(report_dir.join("log.txt"), log_content)?;

    // 4. hashes.json (if provided)
    if let Some(h) = hashes {
        fs::write(
            report_dir.join("hashes.json"),
            serde_json::to_string_pretty(h)?,
        )?;
    }

    println!("Report bundle written to: {:?}", report_dir);
    Ok(report_dir)
}
