// Phoenix OS — Phoenix Recovery: Commands
// File: apps/phoenix-recovery/src/commands.rs

use crate::logging::SessionLogger;
use tauri::State;

/// Get all log entries for the current session (for display in the UI).
#[tauri::command]
pub fn get_session_log(logger: State<SessionLogger>) -> Vec<crate::logging::LogEntry> {
    logger.get_entries()
}

/// Export the full session log as a text string (for save-to-file).
#[tauri::command]
pub fn export_session_log(logger: State<SessionLogger>) -> String {
    logger.export_text()
}
