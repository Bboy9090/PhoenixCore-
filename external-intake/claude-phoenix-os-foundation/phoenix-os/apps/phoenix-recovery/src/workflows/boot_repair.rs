// Phoenix OS — Phoenix Recovery: Boot Repair Workflows
// File: apps/phoenix-recovery/src/workflows/boot_repair.rs
//
// GRUB and MBR repair for systems that won't boot.
// These are DESTRUCTIVE operations — all go through the confirmation gate.
//
// Boot repair workflow (typical):
//   1. User selects the disk containing the broken system
//   2. Phoenix Recovery mounts the system partition(s)
//   3. GRUB is reinstalled into the mounted chroot
//   4. Initramfs is regenerated
//   5. System is unmounted and ready to reboot

use serde::{Deserialize, Serialize};
use std::process::Command;
use std::io::Write;

#[derive(Debug, Serialize, Deserialize)]
pub struct GrubRepairOptions {
    /// Target disk (NOT partition) — e.g. "/dev/sda"
    pub target_disk:     String,
    /// Mount point of the target system's root partition
    pub chroot_root:     String,
    /// UEFI or BIOS mode
    pub firmware_mode:   FirmwareMode,
    /// EFI partition mount point (UEFI only)
    pub efi_mount:       Option<String>,
}

#[derive(Debug, Serialize, Deserialize, PartialEq)]
pub enum FirmwareMode {
    Bios,
    Uefi,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct RepairResult {
    pub success:  bool,
    pub log:      String,
    pub next_steps: Vec<String>,
}

/// Reinstall GRUB into a chrooted target system.
///
/// This is a DESTRUCTIVE operation. The caller must have obtained
/// explicit confirmation via safety::confirm_destructive_operation().
///
/// Steps performed:
///   1. Bind-mount /dev, /proc, /sys into the chroot
///   2. Run grub-install inside the chroot
///   3. Run update-grub inside the chroot
///   4. Run update-initramfs inside the chroot
///   5. Unmount bind mounts
#[tauri::command]
pub fn repair_grub(opts: GrubRepairOptions) -> Result<RepairResult, String> {
    validate_device(&opts.target_disk)?;
    validate_chroot(&opts.chroot_root)?;

    let mut log = String::new();
    let mut success = true;

    macro_rules! step {
        ($label:expr, $cmd:expr, $args:expr) => {{
            log.push_str(&format!("\n[{}]\n", $label));
            match Command::new($cmd).args($args).output() {
                Ok(out) => {
                    let out_str = format!(
                        "{}{}",
                        String::from_utf8_lossy(&out.stdout),
                        String::from_utf8_lossy(&out.stderr)
                    );
                    log.push_str(&out_str);
                    if !out.status.success() {
                        log.push_str(&format!("\n[FAILED with exit {}]\n", out.status.code().unwrap_or(-1)));
                        success = false;
                    } else {
                        log.push_str("[OK]\n");
                    }
                }
                Err(e) => {
                    log.push_str(&format!("[ERROR: {}]\n", e));
                    success = false;
                }
            }
        }};
    }

    let root = &opts.chroot_root;

    // Bind mount /dev /proc /sys into chroot
    step!("Mount /dev",          "mount", ["--bind", "/dev",  &format!("{}/dev",  root)]);
    step!("Mount /dev/pts",      "mount", ["--bind", "/dev/pts", &format!("{}/dev/pts", root)]);
    step!("Mount /proc",         "mount", ["--bind", "/proc", &format!("{}/proc", root)]);
    step!("Mount /sys",          "mount", ["--bind", "/sys",  &format!("{}/sys",  root)]);

    // EFI mount for UEFI targets
    if opts.firmware_mode == FirmwareMode::Uefi {
        if let Some(ref efi_mount) = opts.efi_mount {
            step!("Mount EFI partition", "mount", ["--bind", efi_mount, &format!("{}/boot/efi", root)]);
        }
    }

    // Install GRUB
    match opts.firmware_mode {
        FirmwareMode::Bios => {
            step!("grub-install (BIOS)", "chroot",
                [root.as_str(), "grub-install", "--target=i386-pc", &opts.target_disk]);
        }
        FirmwareMode::Uefi => {
            step!("grub-install (UEFI)", "chroot",
                [root.as_str(), "grub-install", "--target=x86_64-efi",
                 "--efi-directory=/boot/efi", "--bootloader-id=phoenix",
                 "--recheck"]);
        }
    }

    step!("update-grub",      "chroot", [root.as_str(), "update-grub"]);
    step!("update-initramfs", "chroot", [root.as_str(), "update-initramfs", "-u", "-k", "all"]);

    // Unmount bind mounts (in reverse order, best-effort)
    let unmounts = [
        format!("{}/boot/efi", root),
        format!("{}/sys",  root),
        format!("{}/proc", root),
        format!("{}/dev/pts", root),
        format!("{}/dev",  root),
    ];
    for mnt in &unmounts {
        let _ = Command::new("umount").arg(mnt).output();
    }

    log_operation(&opts.target_disk, "grub-repair", if success { "SUCCESS" } else { "PARTIAL_FAILURE" });

    let next_steps = if success {
        vec![
            "Remove the Phoenix OS USB drive.".to_string(),
            "Reboot the system.".to_string(),
            "If GRUB still doesn't appear, verify the boot order in BIOS/UEFI settings.".to_string(),
        ]
    } else {
        vec![
            "Review the log above for specific errors.".to_string(),
            "Verify the correct root partition is mounted at the chroot path.".to_string(),
            "Check that grub-pc (BIOS) or grub-efi-amd64 (UEFI) is installed in the target system.".to_string(),
        ]
    };

    Ok(RepairResult { success, log, next_steps })
}

/// Write a fresh MBR (Master Boot Record) to a disk.
/// This only replaces the first 446 bytes (bootstrap code), not the partition table.
///
/// DESTRUCTIVE: Requires confirmation gate.
#[tauri::command]
pub fn repair_mbr(target_disk: String) -> Result<RepairResult, String> {
    validate_device(&target_disk)?;

    let mut log = String::new();

    // Use grub-install to write MBR bootstrap code only
    let output = Command::new("grub-install")
        .args(["--target=i386-pc", "--recheck", &target_disk])
        .output()
        .map_err(|e| format!("Failed to run grub-install: {}", e))?;

    log.push_str(&String::from_utf8_lossy(&output.stdout));
    log.push_str(&String::from_utf8_lossy(&output.stderr));

    let success = output.status.success();
    log_operation(&target_disk, "mbr-repair", if success { "SUCCESS" } else { "FAILED" });

    Ok(RepairResult {
        success,
        log,
        next_steps: if success {
            vec![
                "MBR bootstrap code written.".to_string(),
                "If the system had a GRUB installation, it should now boot.".to_string(),
                "If not, use the full GRUB Repair workflow.".to_string(),
            ]
        } else {
            vec!["Review the log. Ensure grub-pc is installed.".to_string()]
        },
    })
}

fn validate_device(device: &str) -> Result<(), String> {
    if !device.starts_with("/dev/") {
        return Err(format!("Invalid device path: {}", device));
    }
    if device.contains("..") {
        return Err("Device path must not contain '..'".to_string());
    }
    // Must be a disk (no partition number at end)
    let name = &device[5..];
    if name.chars().last().map(|c| c.is_ascii_digit()).unwrap_or(false)
        && !name.starts_with("nvme")
    {
        return Err(format!(
            "{} looks like a partition, not a disk. GRUB repair targets the disk (e.g. /dev/sda), not a partition.",
            device
        ));
    }
    Ok(())
}

fn validate_chroot(path: &str) -> Result<(), String> {
    if !std::path::Path::new(path).is_dir() {
        return Err(format!("Chroot path is not a directory: {}", path));
    }
    // Basic sanity check: should have /etc inside
    if !std::path::Path::new(&format!("{}/etc", path)).is_dir() {
        return Err(format!(
            "Chroot path {} does not look like a mounted Linux root (no /etc inside).",
            path
        ));
    }
    Ok(())
}

fn log_operation(device: &str, tool: &str, status: &str) {
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
