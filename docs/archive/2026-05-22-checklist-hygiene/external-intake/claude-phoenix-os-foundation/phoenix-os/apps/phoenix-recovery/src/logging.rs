// Phoenix OS — Phoenix Recovery: Session Logger
// File: apps/phoenix-recovery/src/logging.rs
//
// Structured session logging for recovery operations.
// Every recovery session gets a unique log file:
//   /var/log/phoenix/recovery-<session_id>.log
//
// The log is also kept in memory for export and display in the UI.

use serde::{Deserialize, Serialize};
use std::io::Write;
use std::sync::{Arc, Mutex};

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct LogEntry {
    pub timestamp_unix: u64,
    pub level:          LogLevel,
    pub category:       String,  // e.g. "disk", "filesystem", "boot", "system"
    pub message:        String,
    pub detail:         Option<String>,
}

#[derive(Debug, Serialize, Deserialize, Clone, PartialEq)]
pub enum LogLevel {
    Info,
    Success,
    Warning,
    Error,
}

pub struct SessionLogger {
    pub session_id:  u64,
    pub log_path:    String,
    entries:         Arc<Mutex<Vec<LogEntry>>>,
}

impl SessionLogger {
    pub fn new(session_id: u64) -> Self {
        let log_path = format!("/var/log/phoenix/recovery-{}.log", session_id);

        // Write session header
        let header = format!(
            "Phoenix OS Recovery Session\nSession ID : {}\nStarted    : {} UTC\n{}\n\n",
            session_id,
            chrono_now_human(),
            "=".repeat(60),
        );
        let _ = std::fs::write(&log_path, header);

        SessionLogger {
            session_id,
            log_path,
            entries: Arc::new(Mutex::new(Vec::new())),
        }
    }

    pub fn log(&self, level: LogLevel, category: &str, message: &str, detail: Option<&str>) {
        let timestamp = unix_now();

        let entry = LogEntry {
            timestamp_unix: timestamp,
            level: level.clone(),
            category:       category.to_string(),
            message:        message.to_string(),
            detail:         detail.map(String::from),
        };

        // Append to in-memory log
        if let Ok(mut entries) = self.entries.lock() {
            entries.push(entry.clone());
        }

        // Append to log file
        let level_str = match level {
            LogLevel::Info    => "INFO",
            LogLevel::Success => "OK  ",
            LogLevel::Warning => "WARN",
            LogLevel::Error   => "ERR ",
        };

        let mut line = format!(
            "[{}] [{}] [{}] {}",
            timestamp, level_str, category, message
        );
        if let Some(d) = detail {
            line.push_str(&format!("\n         {}", d));
        }
        line.push('\n');

        let _ = std::fs::OpenOptions::new()
            .create(true).append(true)
            .open(&self.log_path)
            .and_then(|mut f| f.write_all(line.as_bytes()));
    }

    pub fn info(&self, category: &str, message: &str) {
        self.log(LogLevel::Info, category, message, None);
    }

    pub fn success(&self, category: &str, message: &str) {
        self.log(LogLevel::Success, category, message, None);
    }

    pub fn warn(&self, category: &str, message: &str) {
        self.log(LogLevel::Warning, category, message, None);
    }

    pub fn error(&self, category: &str, message: &str, detail: Option<&str>) {
        self.log(LogLevel::Error, category, message, detail);
    }

    pub fn get_entries(&self) -> Vec<LogEntry> {
        self.entries.lock()
            .map(|e| e.clone())
            .unwrap_or_default()
    }

    pub fn export_text(&self) -> String {
        std::fs::read_to_string(&self.log_path)
            .unwrap_or_else(|_| "Log file not readable.".to_string())
    }
}

fn unix_now() -> u64 {
    std::time::SystemTime::now()
        .duration_since(std::time::UNIX_EPOCH)
        .map(|d| d.as_secs())
        .unwrap_or(0)
}

fn chrono_now_human() -> String {
    // Simple UTC timestamp without chrono dependency
    unix_now().to_string()
}
