// Phoenix OS — Phoenix Welcome Application
// File: apps/phoenix-control-center/src/main.rs
//
// Tauri 2 application entry point for Phoenix Control Center.
// This is the backend (Rust) side of the Tauri app.
//
// Build: cargo tauri build
// Dev:   cargo tauri dev

#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use tauri::Manager;

mod commands;
mod disk;
mod system;
mod network;

fn main() {
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .invoke_handler(tauri::generate_handler![
            // System information
            commands::get_system_info,
            commands::get_cpu_info,
            commands::get_memory_info,
            commands::get_thermal_info,
            // Systemd services
            system::list_relevant_services,
            // Disk commands
            disk::list_disks,
            disk::get_disk_smart,
            disk::get_disk_info,
            // Network commands
            network::get_network_interfaces,
            network::get_network_status,
        ])
        .setup(|app| {
            // Initialize the Phoenix disk audit log
            let log_dir = std::path::Path::new("/var/log/phoenix");
            if !log_dir.exists() {
                // In live session this is pre-created; in dev, create it
                let _ = std::fs::create_dir_all(log_dir);
            }

            // In development, open devtools
            #[cfg(debug_assertions)]
            {
                let window = app.get_webview_window("main").unwrap();
                window.open_devtools();
            }

            Ok(())
        })
        .run(tauri::generate_context!())
        .expect("Error while running Phoenix Control Center");
}
