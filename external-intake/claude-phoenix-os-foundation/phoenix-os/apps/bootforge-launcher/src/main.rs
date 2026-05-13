// Phoenix OS — BootForge Launcher
// File: apps/bootforge-launcher/src/main.rs
//
// BootForge session management and Phoenix Key hardware integration.
// Monitors udev for Phoenix Key USB insertion and provides a session
// management interface for repair technicians.
//
// Phoenix Key identification:
//   USB VID: 0x1209 (pid.codes open allocation — replace with registered VID)
//   USB PID: 0xB00F (placeholder — replace with registered PID)

#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

mod key;
mod session;
mod commands;

use tauri::Manager;

// Phoenix Key USB identifiers
// TODO: Replace with registered USB VID/PID before hardware production
const PHOENIX_KEY_VID: u16 = 0x1209;
const PHOENIX_KEY_PID: u16 = 0xB00F;

fn main() {
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .invoke_handler(tauri::generate_handler![
            commands::detect_phoenix_key,
            commands::get_key_info,
            commands::read_session_data,
            commands::write_session_data,
            commands::export_session_log,
            commands::launch_recovery,
            commands::launch_control_center,
        ])
        .setup(|app| {
            let app_handle = app.handle().clone();

            // Spawn background thread to monitor for Phoenix Key insertion
            std::thread::spawn(move || {
                key::monitor_usb_events(app_handle, PHOENIX_KEY_VID, PHOENIX_KEY_PID);
            });

            Ok(())
        })
        .run(tauri::generate_context!())
        .expect("Error while running BootForge Launcher");
}
