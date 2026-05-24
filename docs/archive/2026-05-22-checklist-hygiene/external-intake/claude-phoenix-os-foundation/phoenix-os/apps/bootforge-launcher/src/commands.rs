// Phoenix OS — BootForge Launcher: Commands
// File: apps/bootforge-launcher/src/commands.rs

use crate::key::{detect_phoenix_key, PhoenixKeyInfo};
use crate::session::{read_sessions, write_session, BootForgeSession};
use serde::{Deserialize, Serialize};
use std::process::Command;

#[tauri::command]
pub fn detect_phoenix_key() -> PhoenixKeyInfo {
    crate::key::detect_phoenix_key()
}

#[tauri::command]
pub fn get_key_info() -> PhoenixKeyInfo {
    crate::key::detect_phoenix_key()
}

#[tauri::command]
pub fn read_session_data(mount_path: String) -> Result<Vec<BootForgeSession>, String> {
    if mount_path.is_empty() {
        return Err("No mount path provided".to_string());
    }
    Ok(read_sessions(&mount_path))
}

#[tauri::command]
pub fn write_session_data(
    mount_path: String,
    session: BootForgeSession,
) -> Result<(), String> {
    if mount_path.is_empty() {
        return Err("No mount path provided".to_string());
    }
    write_session(&mount_path, &session)
}

#[tauri::command]
pub fn export_session_log(
    session_id: String,
    output_path: String,
) -> Result<String, String> {
    // TODO: Implement session log export to PDF or text
    // For now, return a placeholder
    let _ = (session_id, output_path);
    Ok("Export not yet implemented. Coming in Phase 1.".to_string())
}

#[tauri::command]
pub fn launch_recovery() -> Result<(), String> {
    Command::new("phoenix-recovery")
        .spawn()
        .map(|_| ())
        .map_err(|e| format!("Failed to launch phoenix-recovery: {}", e))
}

#[tauri::command]
pub fn launch_control_center() -> Result<(), String> {
    Command::new("phoenix-control-center")
        .spawn()
        .map(|_| ())
        .map_err(|e| format!("Failed to launch phoenix-control-center: {}", e))
}
