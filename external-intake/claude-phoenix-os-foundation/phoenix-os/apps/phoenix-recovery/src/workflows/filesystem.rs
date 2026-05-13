// Phoenix OS — Phoenix Recovery: Filesystem Workflows
// File: apps/phoenix-recovery/src/workflows/filesystem.rs
//
// Guided filesystem check and repair workflows.
// All operations target explicitly user-selected devices only.
// Destructive operations go through safety.rs confirmation gate first.

use serde::{Deserialize, Serialize};
use std::process::{Command, Stdio};

#[derive(Debug, Serialize, Deserialize)]
pub struct FsckOptions {
    pub device:      String,  // e.g. "/dev/sdb1"
    pub dry_run:     bool,    // true = check only, no repairs (fsck -n)
    pub force:       bool,    // true = force check even if clean (fsck -f)
    pub auto_repair: bool,    // true = auto-fix without prompts (fsck -y) — requires confirmation
}

#[derive(Debug, Serialize, Deserialize)]
pub struct FsckResult {
    pub device:     String,
    pub exit_code:  i32,
    pub output:     String,
    pub errors_found: bool,
    pub errors_fixed: bool,
    pub summary:    String,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct NtfsRepairOptions {
    pub device:  String,
    pub dry_run: bool,
}

/// Run fsck on a partition.
///
/// SAFETY: If `auto_repair` is true (fsck -y), the caller MUST have already
/// obtained explicit user confirmation via safety::confirm_destructive_operation().
#[tauri::command]
pub fn run_fsck(opts: FsckOptions) -> Result<FsckResult, String> {
    validate_device(&opts.device)?;

    let mut args: Vec<&str> = vec![];

    if opts.dry_run {
        args.push("-n");   // No repairs — check only
    } else if opts.auto_repair {
        // auto_repair = true means the caller has already confirmed
        args.push("-y");
    } else {
        args.push("-n");   // Default: dry run (safe)
    }

    if opts.force {
        args.push("-f");
    }

    // Verbose output
    args.push("-v");

    args.push(&opts.device);

    // Run fsck
    // Note: fsck must be run on an unmounted filesystem.
    // The caller (UI) is responsible for ensuring the device is unmounted.
    let output = Command::new("fsck")
        .args(&args)
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .output()
        .map_err(|e| format!("Failed to run fsck: {}", e))?;

    let stdout = String::from_utf8_lossy(&output.stdout).to_string();
    let stderr = String::from_utf8_lossy(&output.stderr).to_string();
    let combined = format!("{}{}", stdout, stderr);
    let exit_code = output.status.code().unwrap_or(-1);

    // fsck exit codes:
    //   0 = no errors
    //   1 = errors corrected
    //   2 = system should be rebooted
    //   4 = errors left uncorrected
    //   8 = operational error
    //  16 = usage error
    //  32 = cancelled
    // 128 = library error
    let errors_found = exit_code != 0;
    let errors_fixed = exit_code == 1;

    let summary = match exit_code {
        0  => "No filesystem errors found.".to_string(),
        1  => "Filesystem errors were found and corrected.".to_string(),
        2  => "Filesystem errors corrected — system reboot recommended.".to_string(),
        4  => "Filesystem errors found but NOT corrected. Run with repair enabled.".to_string(),
        8  => "Operational error during fsck — check device connectivity.".to_string(),
        _  => format!("fsck exited with code {}. Review output for details.", exit_code),
    };

    // Log to audit log
    log_operation(&opts.device, "fsck", if errors_fixed { "REPAIRED" } else { "SCANNED" });

    Ok(FsckResult {
        device: opts.device,
        exit_code,
        output: combined,
        errors_found,
        errors_fixed,
        summary,
    })
}

/// Run ntfsfix on an NTFS partition.
/// ntfsfix is a lightweight NTFS consistency checker — NOT a full repair tool.
/// For full NTFS repair, chkdsk from Windows is required.
#[tauri::command]
pub fn repair_ntfs(opts: NtfsRepairOptions) -> Result<FsckResult, String> {
    validate_device(&opts.device)?;

    if !command_exists("ntfsfix") {
        return Err("ntfsfix not found. Install ntfs-3g package.".to_string());
    }

    let mut args = vec![];

    if opts.dry_run {
        args.push("-n");  // Dry run — no changes
    }

    args.push(opts.device.as_str());

    let output = Command::new("ntfsfix")
        .args(&args)
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .output()
        .map_err(|e| format!("Failed to run ntfsfix: {}", e))?;

    let combined = format!(
        "{}{}",
        String::from_utf8_lossy(&output.stdout),
        String::from_utf8_lossy(&output.stderr)
    );
    let exit_code = output.status.code().unwrap_or(-1);

    let summary = if exit_code == 0 {
        "NTFS volume processed. Boot into Windows and run chkdsk for full repair.".to_string()
    } else {
        format!("ntfsfix exited with code {}. The volume may require Windows chkdsk.", exit_code)
    };

    log_operation(&opts.device, "ntfsfix", "COMPLETED");

    Ok(FsckResult {
        device: opts.device,
        exit_code,
        output: combined,
        errors_found: exit_code != 0,
        errors_fixed: false,  // ntfsfix never guarantees full repair
        summary,
    })
}

// ---- Helpers ----

fn validate_device(device: &str) -> Result<(), String> {
    if !device.starts_with("/dev/") {
        return Err(format!("Invalid device path: {}", device));
    }
    if device.contains("..") {
        return Err("Device path must not contain '..'".to_string());
    }
    if !std::path::Path::new(device).exists() {
        return Err(format!("Device does not exist: {}", device));
    }
    Ok(())
}

fn command_exists(cmd: &str) -> bool {
    Command::new("which").arg(cmd).output()
        .map(|o| o.status.success())
        .unwrap_or(false)
}

fn log_operation(device: &str, tool: &str, status: &str) {
    use std::io::Write;
    let entry = format!(
        "[{}] {} {} {} {}\n",
        std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .map(|d| d.as_secs())
            .unwrap_or(0),
        std::env::var("USER").unwrap_or_else(|_| "phoenix".to_string()),
        tool, device, status
    );
    let _ = std::fs::OpenOptions::new()
        .create(true).append(true)
        .open("/var/log/phoenix/disk-ops.log")
        .and_then(|mut f| f.write_all(entry.as_bytes()));
}
