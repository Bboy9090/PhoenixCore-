use std::fs::File;
use std::io::Write;
use std::path::PathBuf;
use chrono::Local;
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ExportResult {
    pub success: bool,
    pub file_path: String,
    pub file_size: u64,
    pub lines_exported: usize,
    pub export_time: String,
    pub message: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct LogEntry {
    pub timestamp: u64,
    pub level: String,
    pub message: String,
    pub stage: String,
}

pub struct LogExporter;

impl LogExporter {
    /// Export logs to a text file
    pub fn export_to_text(
        logs: Vec<LogEntry>,
        output_path: Option<String>,
    ) -> Result<ExportResult, String> {
        let file_path = output_path.unwrap_or_else(|| {
            let timestamp = Local::now().format("%Y%m%d_%H%M%S");
            format!("phoenix_build_logs_{}.txt", timestamp)
        });

        let mut file = File::create(&file_path)
            .map_err(|e| format!("Failed to create file: {}", e))?;

        let header = Self::generate_header();
        file.write_all(header.as_bytes())
            .map_err(|e| format!("Failed to write header: {}", e))?;

        let mut line_count = 0;
        for log in &logs {
            let formatted = Self::format_log_entry(&log);
            file.write_all(formatted.as_bytes())
                .map_err(|e| format!("Failed to write log: {}", e))?;
            line_count += 1;
        }

        let footer = Self::generate_footer(line_count);
        file.write_all(footer.as_bytes())
            .map_err(|e| format!("Failed to write footer: {}", e))?;

        let file_size = std::fs::metadata(&file_path)
            .map(|m| m.len())
            .unwrap_or(0);

        Ok(ExportResult {
            success: true,
            file_path,
            file_size,
            lines_exported: line_count,
            export_time: Local::now().format("%Y-%m-%d %H:%M:%S").to_string(),
            message: format!("Successfully exported {} log entries", line_count),
        })
    }

    /// Export logs to JSON format
    pub fn export_to_json(
        logs: Vec<LogEntry>,
        output_path: Option<String>,
    ) -> Result<ExportResult, String> {
        let file_path = output_path.unwrap_or_else(|| {
            let timestamp = Local::now().format("%Y%m%d_%H%M%S");
            format!("phoenix_build_logs_{}.json", timestamp)
        });

        let json_data = serde_json::json!({
            "export_metadata": {
                "export_time": Local::now().format("%Y-%m-%d %H:%M:%S").to_string(),
                "total_entries": logs.len(),
                "phoenix_version": "2.0.0",
            },
            "logs": logs,
        });

        let json_string = serde_json::to_string_pretty(&json_data)
            .map_err(|e| format!("Failed to serialize JSON: {}", e))?;

        let mut file = File::create(&file_path)
            .map_err(|e| format!("Failed to create file: {}", e))?;

        file.write_all(json_string.as_bytes())
            .map_err(|e| format!("Failed to write JSON: {}", e))?;

        let file_size = std::fs::metadata(&file_path)
            .map(|m| m.len())
            .unwrap_or(0);

        Ok(ExportResult {
            success: true,
            file_path,
            file_size,
            lines_exported: logs.len(),
            export_time: Local::now().format("%Y-%m-%d %H:%M:%S").to_string(),
            message: format!("Successfully exported {} log entries to JSON", logs.len()),
        })
    }

    /// Export logs to CSV format
    pub fn export_to_csv(
        logs: Vec<LogEntry>,
        output_path: Option<String>,
    ) -> Result<ExportResult, String> {
        let file_path = output_path.unwrap_or_else(|| {
            let timestamp = Local::now().format("%Y%m%d_%H%M%S");
            format!("phoenix_build_logs_{}.csv", timestamp)
        });

        let mut file = File::create(&file_path)
            .map_err(|e| format!("Failed to create file: {}", e))?;

        // Write CSV header
        let header = "Timestamp,Level,Stage,Message\n";
        file.write_all(header.as_bytes())
            .map_err(|e| format!("Failed to write header: {}", e))?;

        let mut line_count = 0;
        for log in &logs {
            let timestamp = Self::format_timestamp(log.timestamp);
            let level = &log.level;
            let stage = &log.stage;
            let message = Self::escape_csv_field(&log.message);

            let line = format!("{},{},{},{}\n", timestamp, level, stage, message);
            file.write_all(line.as_bytes())
                .map_err(|e| format!("Failed to write log: {}", e))?;
            line_count += 1;
        }

        let file_size = std::fs::metadata(&file_path)
            .map(|m| m.len())
            .unwrap_or(0);

        Ok(ExportResult {
            success: true,
            file_path,
            file_size,
            lines_exported: line_count,
            export_time: Local::now().format("%Y-%m-%d %H:%M:%S").to_string(),
            message: format!("Successfully exported {} log entries to CSV", line_count),
        })
    }

    /// Generate header for text export
    fn generate_header() -> String {
        let timestamp = Local::now().format("%Y-%m-%d %H:%M:%S");
        format!(
            "Phoenix OS Build Logs\n\
             Export Date: {}\n\
             Phoenix Version: 2.0.0\n\
             {}\n\n",
            timestamp,
            "=".repeat(80)
        )
    }

    /// Generate footer for text export
    fn generate_footer(line_count: usize) -> String {
        format!(
            "\n{}\n\
             Total Log Entries: {}\n\
             End of Export\n",
            "=".repeat(80),
            line_count
        )
    }

    /// Format a single log entry for text export
    fn format_log_entry(log: &LogEntry) -> String {
        let timestamp = Self::format_timestamp(log.timestamp);
        let level = format!("[{}]", log.level);
        let stage = format!("({})", log.stage);
        format!("{} {} {}: {}\n", timestamp, level, stage, log.message)
    }

    /// Format timestamp from Unix seconds
    fn format_timestamp(timestamp: u64) -> String {
        use chrono::DateTime;
        let datetime = DateTime::<Local>::from(std::time::UNIX_EPOCH + std::time::Duration::from_secs(timestamp));
        datetime.format("%Y-%m-%d %H:%M:%S").to_string()
    }

    /// Escape CSV field values
    fn escape_csv_field(field: &str) -> String {
        if field.contains(',') || field.contains('"') || field.contains('\n') {
            format!("\"{}\"", field.replace('"', "\"\""))
        } else {
            field.to_string()
        }
    }

    /// Get export directory
    pub fn get_export_directory() -> Result<PathBuf, String> {
        #[cfg(target_os = "windows")]
        {
            let path = PathBuf::from(std::env::var("USERPROFILE").unwrap_or_else(|_| ".".to_string()))
                .join("Downloads");
            Ok(path)
        }

        #[cfg(target_os = "macos")]
        {
            let path = PathBuf::from(std::env::var("HOME").unwrap_or_else(|_| ".".to_string()))
                .join("Downloads");
            Ok(path)
        }

        #[cfg(target_os = "linux")]
        {
            let path = PathBuf::from(std::env::var("HOME").unwrap_or_else(|_| ".".to_string()))
                .join("Downloads");
            Ok(path)
        }

        #[cfg(not(any(target_os = "windows", target_os = "macos", target_os = "linux")))]
        {
            Ok(PathBuf::from("."))
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_escape_csv_field() {
        assert_eq!(LogExporter::escape_csv_field("simple"), "simple");
        assert_eq!(LogExporter::escape_csv_field("with,comma"), "\"with,comma\"");
        assert_eq!(LogExporter::escape_csv_field("with\"quote"), "\"with\"\"quote\"");
    }

    #[test]
    fn test_format_timestamp() {
        let timestamp = 1609459200; // 2021-01-01 00:00:00 UTC
        let formatted = LogExporter::format_timestamp(timestamp);
        assert!(!formatted.is_empty());
        assert!(formatted.contains("2021"));
    }
}
