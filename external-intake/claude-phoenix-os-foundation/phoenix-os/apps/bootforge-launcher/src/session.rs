// Phoenix OS — BootForge Launcher: Session Module
// File: apps/bootforge-launcher/src/session.rs
//
// Manages BootForge session data: reading from and writing to the Phoenix Key.
// A "session" is a named workspace on the Phoenix Key that stores:
//   - Client machine information (gathered via phoenix-sysinfo)
//   - Repair log entries
//   - Disk images (if key has sufficient capacity)
//   - Exported recovery reports

use serde::{Deserialize, Serialize};

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct BootForgeSession {
    pub id:          String,
    pub created_at:  u64,       // Unix timestamp
    pub client_name: String,
    pub notes:       String,
    pub log_entries: Vec<LogEntry>,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct LogEntry {
    pub timestamp: u64,
    pub level:     LogLevel,
    pub message:   String,
    pub tool:      String,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
pub enum LogLevel {
    Info,
    Success,
    Warning,
    Error,
}

/// Read all sessions from the Phoenix Key's sessions directory.
pub fn read_sessions(key_mount: &str) -> Vec<BootForgeSession> {
    let sessions_path = format!("{}/bootforge/sessions", key_mount);

    let Ok(entries) = std::fs::read_dir(&sessions_path) else {
        return vec![];
    };

    let mut sessions = Vec::new();

    for entry in entries.flatten() {
        let path = entry.path();
        if path.extension().and_then(|e| e.to_str()) == Some("json") {
            if let Ok(content) = std::fs::read_to_string(&path) {
                if let Ok(session) = serde_json::from_str::<BootForgeSession>(&content) {
                    sessions.push(session);
                }
            }
        }
    }

    // Sort newest first
    sessions.sort_by(|a, b| b.created_at.cmp(&a.created_at));
    sessions
}

/// Write a session to the Phoenix Key.
pub fn write_session(key_mount: &str, session: &BootForgeSession) -> Result<(), String> {
    let sessions_path = format!("{}/bootforge/sessions", key_mount);
    std::fs::create_dir_all(&sessions_path)
        .map_err(|e| format!("Cannot create sessions directory: {}", e))?;

    let file_path = format!("{}/{}.json", sessions_path, session.id);
    let json = serde_json::to_string_pretty(session)
        .map_err(|e| format!("Serialization error: {}", e))?;

    std::fs::write(&file_path, json)
        .map_err(|e| format!("Write error: {}", e))?;

    Ok(())
}
