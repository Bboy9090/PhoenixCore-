// Phoenix OS — BootForge Launcher: Phoenix Key Monitor
// File: apps/bootforge-launcher/src/key.rs
//
// Monitors udev events for Phoenix Key USB insertion and removal.
// Emits Tauri events to the frontend when key state changes.

use serde::{Deserialize, Serialize};
use std::process::Command;
use tauri::AppHandle;

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct PhoenixKeyInfo {
    pub present: bool,
    pub device_path: Option<String>,
    pub mount_path: Option<String>,
    pub serial: Option<String>,
    pub firmware_version: Option<String>,
    pub storage_total_bytes: Option<u64>,
    pub storage_free_bytes: Option<u64>,
}

/// Monitors udev for Phoenix Key insertion and removal.
/// Emits "phoenix-key-inserted" and "phoenix-key-removed" events to the frontend.
///
/// This function blocks indefinitely and should be run in a dedicated thread.
pub fn monitor_usb_events(app_handle: AppHandle, vid: u16, pid: u16) {
    // TODO: Implement using libudev-rs crate for proper udev monitoring
    // For Phase 0, we poll using lsusb as a stub implementation.
    //
    // Phase 1 implementation:
    //   use udev::{MonitorBuilder, EventType};
    //   let monitor = MonitorBuilder::new().match_subsystem("usb").listen();
    //   for event in monitor.iter() {
    //       if event.event_type() == EventType::Add { ... }
    //   }

    let mut key_was_present = false;

    loop {
        let key_present = check_key_present_lsusb(vid, pid);

        if key_present && !key_was_present {
            // Key was just inserted
            let key_info = get_key_info_internal(vid, pid);
            let _ = app_handle.emit("phoenix-key-inserted", &key_info);
            key_was_present = true;
        } else if !key_present && key_was_present {
            // Key was just removed
            let _ = app_handle.emit("phoenix-key-removed", ());
            key_was_present = false;
        }

        std::thread::sleep(std::time::Duration::from_millis(500));
    }
}

/// Check if a USB device with the given VID:PID is connected using lsusb.
/// Returns true if the device is present.
fn check_key_present_lsusb(vid: u16, pid: u16) -> bool {
    let vid_str = format!("{:04x}", vid);
    let pid_str = format!("{:04x}", pid);
    let target = format!("{}:{}", vid_str, pid_str);

    let output = Command::new("lsusb")
        .output()
        .unwrap_or_default();

    let lsusb_str = String::from_utf8_lossy(&output.stdout);
    lsusb_str.to_lowercase().contains(&target)
}

/// Get detailed information about the connected Phoenix Key.
fn get_key_info_internal(vid: u16, pid: u16) -> PhoenixKeyInfo {
    let present = check_key_present_lsusb(vid, pid);

    if !present {
        return PhoenixKeyInfo {
            present: false,
            device_path: None,
            mount_path: None,
            serial: None,
            firmware_version: None,
            storage_total_bytes: None,
            storage_free_bytes: None,
        };
    }

    // TODO: Find the block device path for this USB VID:PID using udevadm
    // udevadm info --export-db | grep -A 20 "ID_VENDOR_ID=1209"

    PhoenixKeyInfo {
        present: true,
        device_path: None, // TODO: Resolve via udevadm
        mount_path: None,  // TODO: Check /proc/mounts
        serial: None,      // TODO: Read from udev ID_SERIAL_SHORT
        firmware_version: None, // TODO: Read from key's metadata partition
        storage_total_bytes: None,
        storage_free_bytes: None,
    }
}

/// Public command: detect if Phoenix Key is present.
#[tauri::command]
pub fn detect_phoenix_key() -> PhoenixKeyInfo {
    get_key_info_internal(
        super::PHOENIX_KEY_VID,
        super::PHOENIX_KEY_PID,
    )
}

#[tauri::command]
pub fn get_key_info() -> PhoenixKeyInfo {
    detect_phoenix_key()
}
