/// System recovery and logging module
/// 
/// Provides system log retrieval, recovery point management, and system restoration

use serde::{Deserialize, Serialize};
use std::process::Command;
use std::fs;
use std::path::PathBuf;
use chrono::{DateTime, Utc};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RecoveryPoint {
    pub id: String,
    pub name: String,
    pub description: String,
    pub created_at: String,
    pub size_mb: u64,
    pub point_type: String, // "system", "user", "custom"
    pub status: String, // "active", "archived", "corrupted"
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SystemLog {
    pub timestamp: String,
    pub level: String, // "INFO", "WARNING", "ERROR"
    pub service: String,
    pub message: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BackupInfo {
    pub id: String,
    pub name: String,
    pub location: String,
    pub size_mb: u64,
    pub created_at: String,
    pub status: String,
    pub progress: f32,
}

/// Get system logs from journalctl
pub fn get_system_logs(lines: usize) -> Result<Vec<SystemLog>, String> {
    let output = Command::new("journalctl")
        .arg("-n")
        .arg(lines.to_string())
        .arg("-o")
        .arg("json")
        .output()
        .map_err(|e| format!("Failed to get system logs: {}", e))?;

    if !output.status.success() {
        return Err("Failed to retrieve system logs".to_string());
    }

    let stdout = String::from_utf8_lossy(&output.stdout);
    let mut logs = Vec::new();

    for line in stdout.lines() {
        if let Ok(json) = serde_json::from_str::<serde_json::Value>(line) {
            let log = SystemLog {
                timestamp: json["__REALTIME_TIMESTAMP"]
                    .as_str()
                    .unwrap_or("Unknown")
                    .to_string(),
                level: json["PRIORITY"]
                    .as_str()
                    .unwrap_or("INFO")
                    .to_string(),
                service: json["_SYSTEMD_UNIT"]
                    .as_str()
                    .unwrap_or("system")
                    .to_string(),
                message: json["MESSAGE"]
                    .as_str()
                    .unwrap_or("")
                    .to_string(),
            };
            logs.push(log);
        }
    }

    Ok(logs)
}

/// Get kernel logs
pub fn get_kernel_logs(lines: usize) -> Result<Vec<String>, String> {
    let output = Command::new("dmesg")
        .arg("-T")
        .output()
        .map_err(|e| format!("Failed to get kernel logs: {}", e))?;

    let stdout = String::from_utf8_lossy(&output.stdout);
    let logs: Vec<String> = stdout
        .lines()
        .rev()
        .take(lines)
        .map(|s| s.to_string())
        .collect();

    Ok(logs)
}

/// Get application logs
pub fn get_application_logs(app_name: &str, lines: usize) -> Result<Vec<String>, String> {
    let log_paths = vec![
        format!("/var/log/{}.log", app_name),
        format!("~/.local/share/{}/logs/app.log", app_name),
        format!("/home/{}/.config/{}/logs.txt", std::env::var("USER").unwrap_or_default(), app_name),
    ];

    for path in log_paths {
        if let Ok(content) = fs::read_to_string(&path) {
            let logs: Vec<String> = content
                .lines()
                .rev()
                .take(lines)
                .map(|s| s.to_string())
                .collect();
            return Ok(logs);
        }
    }

    Err(format!("No logs found for application: {}", app_name))
}

/// Create a recovery point
pub fn create_recovery_point(name: &str, description: &str) -> Result<RecoveryPoint, String> {
    let id = format!("rp_{}", uuid::Uuid::new_v4());
    let recovery_dir = PathBuf::from(format!("/var/lib/phoenix/recovery/{}", id));

    // Create recovery directory
    fs::create_dir_all(&recovery_dir)
        .map_err(|e| format!("Failed to create recovery directory: {}", e))?;

    // Backup important system files
    backup_system_files(&recovery_dir)?;

    // Calculate size
    let size_mb = calculate_directory_size(&recovery_dir)?;

    let point = RecoveryPoint {
        id,
        name: name.to_string(),
        description: description.to_string(),
        created_at: Utc::now().to_rfc3339(),
        size_mb,
        point_type: "custom".to_string(),
        status: "active".to_string(),
    };

    // Save metadata
    save_recovery_metadata(&point)?;

    Ok(point)
}

/// List all recovery points
pub fn list_recovery_points() -> Result<Vec<RecoveryPoint>, String> {
    let recovery_base = PathBuf::from("/var/lib/phoenix/recovery");

    if !recovery_base.exists() {
        return Ok(Vec::new());
    }

    let mut points = Vec::new();

    for entry in fs::read_dir(&recovery_base)
        .map_err(|e| format!("Failed to read recovery directory: {}", e))?
    {
        let entry = entry.map_err(|e| format!("Failed to read entry: {}", e))?;
        let path = entry.path();

        if path.is_dir() {
            if let Ok(metadata) = load_recovery_metadata(&path) {
                points.push(metadata);
            }
        }
    }

    // Sort by creation date (newest first)
    points.sort_by(|a, b| b.created_at.cmp(&a.created_at));

    Ok(points)
}

/// Restore from recovery point
pub fn restore_recovery_point(recovery_id: &str) -> Result<String, String> {
    let recovery_path = PathBuf::from(format!("/var/lib/phoenix/recovery/{}", recovery_id));

    if !recovery_path.exists() {
        return Err("Recovery point not found".to_string());
    }

    // Verify recovery point integrity
    verify_recovery_point(&recovery_path)?;

    // Perform restoration
    restore_system_files(&recovery_path)?;

    Ok(format!("System restored from recovery point: {}", recovery_id))
}

/// Delete recovery point
pub fn delete_recovery_point(recovery_id: &str) -> Result<String, String> {
    let recovery_path = PathBuf::from(format!("/var/lib/phoenix/recovery/{}", recovery_id));

    if !recovery_path.exists() {
        return Err("Recovery point not found".to_string());
    }

    fs::remove_dir_all(&recovery_path)
        .map_err(|e| format!("Failed to delete recovery point: {}", e))?;

    Ok(format!("Recovery point deleted: {}", recovery_id))
}

/// Clear old logs
pub fn clear_old_logs(days: u32) -> Result<String, String> {
    let output = Command::new("journalctl")
        .arg("--vacuum-time")
        .arg(format!("{}d", days))
        .output()
        .map_err(|e| format!("Failed to clear logs: {}", e))?;

    if output.status.success() {
        Ok(format!("Logs older than {} days cleared", days))
    } else {
        Err("Failed to clear logs".to_string())
    }
}

/// Export logs to file
pub fn export_logs(output_path: &str, format: &str) -> Result<String, String> {
    let logs = get_system_logs(1000)?;

    match format {
        "json" => {
            let json = serde_json::to_string_pretty(&logs)
                .map_err(|e| format!("Failed to serialize logs: {}", e))?;
            fs::write(output_path, json)
                .map_err(|e| format!("Failed to write logs: {}", e))?;
        }
        "csv" => {
            let mut csv = String::from("timestamp,level,service,message\n");
            for log in logs {
                csv.push_str(&format!(
                    "\"{}\",\"{}\",\"{}\",\"{}\"\n",
                    log.timestamp, log.level, log.service, log.message
                ));
            }
            fs::write(output_path, csv)
                .map_err(|e| format!("Failed to write logs: {}", e))?;
        }
        "txt" => {
            let mut text = String::new();
            for log in logs {
                text.push_str(&format!(
                    "[{}] {} [{}] {}\n",
                    log.timestamp, log.level, log.service, log.message
                ));
            }
            fs::write(output_path, text)
                .map_err(|e| format!("Failed to write logs: {}", e))?;
        }
        _ => return Err(format!("Unsupported format: {}", format)),
    }

    Ok(format!("Logs exported to: {}", output_path))
}

// Helper functions

fn backup_system_files(recovery_dir: &PathBuf) -> Result<(), String> {
    // Backup important system files
    let files_to_backup = vec![
        "/etc/fstab",
        "/etc/hostname",
        "/etc/hosts",
        "/boot/grub/grub.cfg",
    ];

    for file in files_to_backup {
        if PathBuf::from(file).exists() {
            let filename = PathBuf::from(file)
                .file_name()
                .unwrap()
                .to_string_lossy()
                .to_string();
            let dest = recovery_dir.join(&filename);
            fs::copy(file, dest)
                .map_err(|e| format!("Failed to backup {}: {}", file, e))?;
        }
    }

    Ok(())
}

fn restore_system_files(recovery_path: &PathBuf) -> Result<(), String> {
    for entry in fs::read_dir(recovery_path)
        .map_err(|e| format!("Failed to read recovery directory: {}", e))?
    {
        let entry = entry.map_err(|e| format!("Failed to read entry: {}", e))?;
        let path = entry.path();

        if path.is_file() {
            let filename = path.file_name().unwrap().to_string_lossy().to_string();
            let dest = format!("/etc/{}", filename);

            fs::copy(&path, &dest)
                .map_err(|e| format!("Failed to restore {}: {}", filename, e))?;
        }
    }

    Ok(())
}

fn calculate_directory_size(path: &PathBuf) -> Result<u64, String> {
    let mut size = 0;

    for entry in fs::read_dir(path)
        .map_err(|e| format!("Failed to read directory: {}", e))?
    {
        let entry = entry.map_err(|e| format!("Failed to read entry: {}", e))?;
        let metadata = entry.metadata()
            .map_err(|e| format!("Failed to get metadata: {}", e))?;

        if metadata.is_file() {
            size += metadata.len();
        } else if metadata.is_dir() {
            size += calculate_directory_size(&entry.path())?;
        }
    }

    Ok(size / 1024 / 1024) // Convert to MB
}

fn save_recovery_metadata(point: &RecoveryPoint) -> Result<(), String> {
    let metadata_path = PathBuf::from(format!("/var/lib/phoenix/recovery/{}/metadata.json", point.id));
    let json = serde_json::to_string_pretty(point)
        .map_err(|e| format!("Failed to serialize metadata: {}", e))?;
    fs::write(metadata_path, json)
        .map_err(|e| format!("Failed to write metadata: {}", e))
}

fn load_recovery_metadata(path: &PathBuf) -> Result<RecoveryPoint, String> {
    let metadata_path = path.join("metadata.json");
    let json = fs::read_to_string(metadata_path)
        .map_err(|e| format!("Failed to read metadata: {}", e))?;
    serde_json::from_str(&json)
        .map_err(|e| format!("Failed to parse metadata: {}", e))
}

fn verify_recovery_point(path: &PathBuf) -> Result<(), String> {
    let metadata_path = path.join("metadata.json");

    if !metadata_path.exists() {
        return Err("Recovery point metadata not found".to_string());
    }

    // Verify all backup files exist
    for entry in fs::read_dir(path)
        .map_err(|e| format!("Failed to read recovery directory: {}", e))?
    {
        let entry = entry.map_err(|e| format!("Failed to read entry: {}", e))?;
        let metadata = entry.metadata()
            .map_err(|e| format!("Failed to get metadata: {}", e))?;

        if metadata.len() == 0 && entry.path().is_file() {
            return Err("Corrupted recovery point: empty file detected".to_string());
        }
    }

    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_recovery_point_creation() {
        let point = RecoveryPoint {
            id: "test_id".to_string(),
            name: "Test Point".to_string(),
            description: "Test description".to_string(),
            created_at: Utc::now().to_rfc3339(),
            size_mb: 100,
            point_type: "custom".to_string(),
            status: "active".to_string(),
        };

        assert_eq!(point.name, "Test Point");
        assert_eq!(point.point_type, "custom");
    }

    #[test]
    fn test_calculate_directory_size() {
        // This would need a temporary directory for testing
        // Skipping for now
    }
}
