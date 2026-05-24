// Phoenix OS — Phoenix Recovery: Data Rescue Workflows
// File: apps/phoenix-recovery/src/workflows/data_rescue.rs
//
// Wrappers for GNU ddrescue and PhotoRec/TestDisk data recovery tools.
// These are read-biased operations (reading from a damaged source).
//
// SAFETY: ddrescue writes an IMAGE FILE, not directly to a disk.
// The output path validation ensures the target is a file path, not a device.

use serde::{Deserialize, Serialize};
use std::process::{Command, Stdio};
use std::io::{BufRead, BufReader};

#[derive(Debug, Serialize, Deserialize)]
pub struct DdrescueOptions {
    /// Source device to read from (e.g. "/dev/sdb")
    pub source_device: String,
    /// Destination image file path (e.g. "/mnt/usb/rescue.img")
    pub output_image:  String,
    /// ddrescue mapfile path for resumable sessions
    pub mapfile:       String,
    /// Retry count for bad sectors (0 = skip, higher = slower but more thorough)
    pub retry_passes:  u32,
    /// Direct I/O (bypass OS cache — better for failing drives)
    pub direct_io:     bool,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct DdrescueStatus {
    pub running:          bool,
    pub rescued_bytes:    u64,
    pub errsize_bytes:    u64,
    pub current_rate_bps: u64,
    pub errors:           u64,
    pub time_elapsed_secs: u64,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct PhotorecOptions {
    /// Source device or partition (e.g. "/dev/sdb" or "/dev/sdb1")
    pub source_device: String,
    /// Output directory for recovered files
    pub output_dir:    String,
    /// File types to recover (empty = all types)
    pub file_types:    Vec<String>,
}

/// Launch GNU ddrescue in a subprocess.
///
/// Returns immediately — ddrescue runs in the background.
/// Progress is read via the mapfile.
///
/// SAFETY CONTRACT: The caller must have:
///   1. Confirmed the source device with the user (show model + serial)
///   2. Confirmed the output path is on a different device (not source)
///   3. Verified sufficient space on the output device
#[tauri::command]
pub fn start_ddrescue(opts: DdrescueOptions) -> Result<String, String> {
    validate_source_device(&opts.source_device)?;
    validate_output_path(&opts.output_image)?;
    validate_mapfile_path(&opts.mapfile)?;

    // Ensure output directory exists
    if let Some(parent) = std::path::Path::new(&opts.output_image).parent() {
        std::fs::create_dir_all(parent)
            .map_err(|e| format!("Cannot create output directory: {}", e))?;
    }

    let mut args = vec![
        "--verbose".to_string(),
        format!("--retry-passes={}", opts.retry_passes),
    ];

    if opts.direct_io {
        args.push("--idirect".to_string());  // Direct I/O on input
    }

    args.push(opts.source_device.clone());
    args.push(opts.output_image.clone());
    args.push(opts.mapfile.clone());

    // Launch ddrescue in background
    let child = Command::new("ddrescue")
        .args(&args)
        .stdout(Stdio::null())
        .stderr(Stdio::null())
        .spawn()
        .map_err(|e| format!("Failed to launch ddrescue: {}", e))?;

    let pid = child.id();

    log_operation(
        &opts.source_device,
        "ddrescue",
        &format!("STARTED pid={} output={}", pid, opts.output_image),
    );

    Ok(format!("ddrescue started (pid {}). Monitor progress via mapfile: {}", pid, opts.mapfile))
}

/// Parse the ddrescue mapfile to get current progress.
/// The mapfile format is documented in the GNU ddrescue manual.
#[tauri::command]
pub fn get_ddrescue_status(mapfile_path: String) -> Result<DdrescueStatus, String> {
    if !std::path::Path::new(&mapfile_path).exists() {
        return Ok(DdrescueStatus {
            running: false,
            rescued_bytes: 0,
            errsize_bytes: 0,
            current_rate_bps: 0,
            errors: 0,
            time_elapsed_secs: 0,
        });
    }

    let content = std::fs::read_to_string(&mapfile_path)
        .map_err(|e| format!("Cannot read mapfile: {}", e))?;

    // ddrescue mapfile status line format:
    // # current_pos  current_status  current_pass
    // # rescued      errsize         errors  current-rate  average-rate  time
    let mut rescued_bytes    = 0u64;
    let mut errsize_bytes    = 0u64;
    let mut errors           = 0u64;
    let mut current_rate_bps = 0u64;
    let mut time_elapsed     = 0u64;

    for line in content.lines() {
        if line.starts_with('#') {
            let parts: Vec<&str> = line[1..].split_whitespace().collect();
            // Try to parse the status summary line (6+ fields, first is hex bytes rescued)
            if parts.len() >= 5 {
                if let Ok(r) = parse_size(parts[0]) { rescued_bytes = r; }
                if let Ok(e) = parse_size(parts[1]) { errsize_bytes = e; }
                if let Ok(n) = parts[2].parse::<u64>() { errors = n; }
                if let Ok(rate) = parse_size(parts[3]) { current_rate_bps = rate; }
                if let Ok(t) = parts[5].parse::<u64>() { time_elapsed = t; }
            }
        }
    }

    Ok(DdrescueStatus {
        running: true,  // TODO: Check if ddrescue process is still alive via pid file
        rescued_bytes,
        errsize_bytes,
        current_rate_bps,
        errors,
        time_elapsed_secs: time_elapsed,
    })
}

/// Launch PhotoRec for file carving (signature-based recovery).
/// PhotoRec writes recovered files to the output_dir.
///
/// Note: PhotoRec has an interactive TUI — this launches it in a terminal window.
#[tauri::command]
pub fn run_photorec(opts: PhotorecOptions) -> Result<String, String> {
    validate_source_device(&opts.source_device)?;

    // Ensure output directory exists
    std::fs::create_dir_all(&opts.output_dir)
        .map_err(|e| format!("Cannot create output directory: {}", e))?;

    // PhotoRec is interactive — open in terminal
    let photorec_cmd = format!(
        "sudo photorec /d {} {}",
        opts.output_dir,
        opts.source_device
    );

    Command::new("phoenix-open-terminal")
        .args(["Phoenix Recovery — PhotoRec"])
        .env("PHOENIX_RUN_CMD", &photorec_cmd)
        .spawn()
        .map_err(|e| format!("Failed to open terminal for photorec: {}", e))?;

    log_operation(&opts.source_device, "photorec", "LAUNCHED");

    Ok(format!(
        "PhotoRec launched in terminal. Recovered files will be written to: {}",
        opts.output_dir
    ))
}

// ---- Validation helpers ----

fn validate_source_device(device: &str) -> Result<(), String> {
    if !device.starts_with("/dev/") {
        return Err(format!("Source must be a device path (e.g. /dev/sdb): {}", device));
    }
    if !std::path::Path::new(device).exists() {
        return Err(format!("Source device not found: {}", device));
    }
    Ok(())
}

fn validate_output_path(path: &str) -> Result<(), String> {
    // Output must NOT be a device path — it should be a file path
    if path.starts_with("/dev/") {
        return Err(
            "Output path must be a FILE path, not a device path. \
             Example: /mnt/usb/rescue.img".to_string()
        );
    }
    if path.is_empty() {
        return Err("Output path cannot be empty.".to_string());
    }
    Ok(())
}

fn validate_mapfile_path(path: &str) -> Result<(), String> {
    if path.starts_with("/dev/") {
        return Err("Mapfile path must not be a device.".to_string());
    }
    if path.is_empty() {
        return Err("Mapfile path cannot be empty.".to_string());
    }
    Ok(())
}

fn parse_size(s: &str) -> Result<u64, String> {
    // ddrescue uses decimal suffixes: B, kB, MB, GB, TB
    let s = s.trim().trim_end_matches('B');
    if let Ok(n) = s.parse::<u64>() {
        return Ok(n);
    }
    let (num, suffix) = s.split_at(s.len().saturating_sub(1));
    let base: u64 = num.parse().map_err(|_| format!("Cannot parse size: {}", s))?;
    Ok(match suffix {
        "k" | "K" => base * 1_000,
        "M"       => base * 1_000_000,
        "G"       => base * 1_000_000_000,
        "T"       => base * 1_000_000_000_000,
        _         => base,
    })
}

fn log_operation(device: &str, tool: &str, status: &str) {
    use std::io::Write;
    let entry = format!(
        "[{}] {} {} {} {}\n",
        std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .map(|d| d.as_secs()).unwrap_or(0),
        std::env::var("USER").unwrap_or_else(|_| "phoenix".to_string()),
        tool, device, status
    );
    let _ = std::fs::OpenOptions::new()
        .create(true).append(true)
        .open("/var/log/phoenix/disk-ops.log")
        .and_then(|mut f| f.write_all(entry.as_bytes()));
}
