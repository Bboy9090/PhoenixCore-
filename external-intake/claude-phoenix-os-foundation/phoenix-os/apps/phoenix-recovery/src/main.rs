// Phoenix OS — Phoenix Recovery Application
// File: apps/phoenix-recovery/src/main.rs
//
// Guided data rescue and system repair workflow application.
// Provides step-by-step interfaces for common recovery scenarios.
//
// SAFETY MODEL:
//   - All destructive operations require explicit device selection by the user
//   - Device path is displayed prominently (model + serial + path) before any operation
//   - User must type the device path to confirm destructive operations
//   - All operations are logged to /var/log/phoenix/recovery-<session>.log

#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use tauri::Manager;
use std::time::{SystemTime, UNIX_EPOCH};

mod commands;
mod workflows;
mod safety;
mod logging;

fn main() {
    // Initialize session log
    let session_id = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap_or_default()
        .as_secs();

    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .manage(logging::SessionLogger::new(session_id))
        .invoke_handler(tauri::generate_handler![
            // Recovery workflows — filesystem
            workflows::filesystem::run_fsck,
            workflows::filesystem::repair_ntfs,
            // Recovery workflows — data rescue
            workflows::data_rescue::start_ddrescue,
            workflows::data_rescue::get_ddrescue_status,
            workflows::data_rescue::run_photorec,
            // Recovery workflows — boot repair
            workflows::boot_repair::repair_grub,
            workflows::boot_repair::repair_mbr,
            // Safety confirmation gate
            safety::confirm_destructive_operation,
            safety::get_device_details,
            // Session logging
            commands::get_session_log,
            commands::export_session_log,
        ])
        .setup(|_app| {
            // Ensure log directory exists
            std::fs::create_dir_all("/var/log/phoenix")
                .unwrap_or_else(|_| {
                    // In dev or if permissions fail, log to /tmp
                });
            Ok(())
        })
        .run(tauri::generate_context!())
        .expect("Error while running Phoenix Recovery");
}
