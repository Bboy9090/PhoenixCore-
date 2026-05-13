/// Build Monitoring Module
/// 
/// Provides real-time monitoring of Phoenix OS ISO builds with log streaming,
/// progress tracking, and build control (pause/resume/cancel).
/// 
/// Features:
/// - Live log streaming from live-build process
/// - Progress percentage calculation
/// - Build stage tracking
/// - Process control (pause, resume, cancel)
/// - Error detection and reporting
/// - Build statistics and metrics

use std::fs::File;
use std::io::{BufRead, BufReader, Write};
use std::path::PathBuf;
use std::process::{Child, Command, Stdio};
use std::sync::{Arc, Mutex};
use std::thread;
use std::time::{SystemTime, UNIX_EPOCH};
use serde::{Deserialize, Serialize};

/// Build stage enumeration
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub enum BuildStage {
    #[serde(rename = "initializing")]
    Initializing,
    #[serde(rename = "verifying")]
    Verifying,
    #[serde(rename = "debootstrap")]
    Debootstrap,
    #[serde(rename = "installing_packages")]
    InstallingPackages,
    #[serde(rename = "customizing")]
    Customizing,
    #[serde(rename = "building_iso")]
    BuildingISO,
    #[serde(rename = "generating_checksums")]
    GeneratingChecksums,
    #[serde(rename = "completed")]
    Completed,
    #[serde(rename = "failed")]
    Failed,
    #[serde(rename = "cancelled")]
    Cancelled,
}

/// Build status structure
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BuildStatus {
    pub is_running: bool,
    pub is_paused: bool,
    pub stage: BuildStage,
    pub progress: u32,
    pub total_lines: u32,
    pub current_line: u32,
    pub elapsed_time: u64,
    pub estimated_time_remaining: u64,
    pub iso_path: Option<String>,
    pub iso_size: Option<u64>,
    pub error_message: Option<String>,
    pub start_time: u64,
    pub end_time: Option<u64>,
    pub build_id: String,
}

/// Log entry structure
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct LogEntry {
    pub timestamp: u64,
    pub level: String,
    pub message: String,
    pub stage: BuildStage,
}

/// Build process manager
pub struct BuildManager {
    process: Option<Child>,
    status: Arc<Mutex<BuildStatus>>,
    log_file: Option<PathBuf>,
    paused: Arc<Mutex<bool>>,
}

impl BuildManager {
    /// Create a new build manager
    pub fn new() -> Self {
        let build_id = format!(
            "build-{}",
            SystemTime::now()
                .duration_since(UNIX_EPOCH)
                .unwrap_or_default()
                .as_secs()
        );

        let status = BuildStatus {
            is_running: false,
            is_paused: false,
            stage: BuildStage::Initializing,
            progress: 0,
            total_lines: 0,
            current_line: 0,
            elapsed_time: 0,
            estimated_time_remaining: 0,
            iso_path: None,
            iso_size: None,
            error_message: None,
            start_time: 0,
            end_time: None,
            build_id,
        };

        BuildManager {
            process: None,
            status: Arc::new(Mutex::new(status)),
            log_file: None,
            paused: Arc::new(Mutex::new(false)),
        }
    }

    /// Start a new build process
    pub fn start_build(&mut self, build_dir: PathBuf) -> Result<(), String> {
        // Verify build directory exists
        if !build_dir.exists() {
            return Err(format!("Build directory does not exist: {:?}", build_dir));
        }

        // Create log file
        let log_path = build_dir.join("build.log");
        let log_file = File::create(&log_path)
            .map_err(|e| format!("Failed to create log file: {}", e))?;

        // Update status
        {
            let mut status = self.status.lock().unwrap();
            status.is_running = true;
            status.is_paused = false;
            status.stage = BuildStage::Verifying;
            status.progress = 5;
            status.start_time = SystemTime::now()
                .duration_since(UNIX_EPOCH)
                .unwrap_or_default()
                .as_secs();
            status.error_message = None;
        }

        // Start build process
        let child = Command::new("bash")
            .arg("scripts/build-iso.sh")
            .current_dir(&build_dir)
            .stdout(Stdio::piped())
            .stderr(Stdio::piped())
            .spawn()
            .map_err(|e| format!("Failed to start build process: {}", e))?;

        self.process = Some(child);
        self.log_file = Some(log_path);

        // Spawn log monitoring thread
        self.spawn_log_monitor();

        Ok(())
    }

    /// Spawn a thread to monitor build logs
    fn spawn_log_monitor(&self) {
        let status = Arc::clone(&self.status);
        let paused = Arc::clone(&self.paused);
        let log_file = self.log_file.clone();

        thread::spawn(move || {
            if let Some(log_path) = log_file {
                loop {
                    // Check if build is still running
                    {
                        let s = status.lock().unwrap();
                        if !s.is_running {
                            break;
                        }
                    }

                    // Check if paused
                    if *paused.lock().unwrap() {
                        thread::sleep(std::time::Duration::from_millis(500));
                        continue;
                    }

                    // Read and process log file
                    if let Ok(file) = File::open(&log_path) {
                        let reader = BufReader::new(file);
                        let mut line_count = 0;

                        for line in reader.lines() {
                            if let Ok(log_line) = line {
                                line_count += 1;
                                Self::process_log_line(&status, &log_line);
                            }
                        }

                        // Update line count
                        {
                            let mut s = status.lock().unwrap();
                            s.current_line = line_count;
                            if s.total_lines == 0 {
                                s.total_lines = line_count * 2; // Estimate total
                            }
                            s.progress = ((line_count as f32 / s.total_lines as f32) * 100.0)
                                .min(99.0) as u32;

                            // Calculate elapsed time
                            let elapsed = SystemTime::now()
                                .duration_since(UNIX_EPOCH)
                                .unwrap_or_default()
                                .as_secs()
                                - s.start_time;
                            s.elapsed_time = elapsed;

                            // Estimate remaining time
                            if s.progress > 0 {
                                let estimated_total =
                                    (elapsed as f32 / (s.progress as f32 / 100.0)) as u64;
                                s.estimated_time_remaining = estimated_total.saturating_sub(elapsed);
                            }
                        }
                    }

                    thread::sleep(std::time::Duration::from_millis(500));
                }
            }
        });
    }

    /// Process a single log line and update build status
    fn process_log_line(status: &Arc<Mutex<BuildStatus>>, line: &str) {
        let mut s = status.lock().unwrap();

        // Detect build stage from log content
        if line.contains("Verifying prerequisites") {
            s.stage = BuildStage::Verifying;
            s.progress = 10;
        } else if line.contains("Debootstrap") || line.contains("bootstrap") {
            s.stage = BuildStage::Debootstrap;
            s.progress = 25;
        } else if line.contains("Installing packages") || line.contains("apt-get install") {
            s.stage = BuildStage::InstallingPackages;
            s.progress = 45;
        } else if line.contains("Customizing") || line.contains("custom") {
            s.stage = BuildStage::Customizing;
            s.progress = 65;
        } else if line.contains("Building ISO") || line.contains("xorriso") {
            s.stage = BuildStage::BuildingISO;
            s.progress = 80;
        } else if line.contains("Generating checksums") || line.contains("sha256sum") {
            s.stage = BuildStage::GeneratingChecksums;
            s.progress = 95;
        } else if line.contains("Build complete") || line.contains("successfully") {
            s.stage = BuildStage::Completed;
            s.progress = 100;
            s.is_running = false;
            s.end_time = Some(
                SystemTime::now()
                    .duration_since(UNIX_EPOCH)
                    .unwrap_or_default()
                    .as_secs(),
            );

            // Extract ISO path if present
            if let Some(iso_path) = Self::extract_iso_path(line) {
                s.iso_path = Some(iso_path);
            }
        } else if line.contains("Error") || line.contains("error") || line.contains("failed") {
            s.stage = BuildStage::Failed;
            s.is_running = false;
            s.error_message = Some(line.to_string());
            s.end_time = Some(
                SystemTime::now()
                    .duration_since(UNIX_EPOCH)
                    .unwrap_or_default()
                    .as_secs(),
            );
        }
    }

    /// Extract ISO path from log line
    fn extract_iso_path(line: &str) -> Option<String> {
        if line.contains(".iso") {
            // Simple extraction - look for .iso file path
            if let Some(start) = line.find('/') {
                if let Some(end) = line[start..].find(".iso") {
                    return Some(line[start..start + end + 4].to_string());
                }
            }
        }
        None
    }

    /// Pause the build process
    pub fn pause_build(&mut self) -> Result<(), String> {
        let mut status = self.status.lock().unwrap();
        if !status.is_running {
            return Err("Build is not running".to_string());
        }

        status.is_paused = true;
        *self.paused.lock().unwrap() = true;

        // Send SIGSTOP to process
        if let Some(ref mut process) = self.process {
            #[cfg(unix)]
            {
                use std::os::unix::process::CommandExt;
                let _ = Command::new("kill")
                    .arg("-STOP")
                    .arg(process.id().to_string())
                    .output();
            }
        }

        Ok(())
    }

    /// Resume the build process
    pub fn resume_build(&mut self) -> Result<(), String> {
        let mut status = self.status.lock().unwrap();
        if !status.is_running {
            return Err("Build is not running".to_string());
        }

        status.is_paused = false;
        *self.paused.lock().unwrap() = false;

        // Send SIGCONT to process
        if let Some(ref mut process) = self.process {
            #[cfg(unix)]
            {
                use std::os::unix::process::CommandExt;
                let _ = Command::new("kill")
                    .arg("-CONT")
                    .arg(process.id().to_string())
                    .output();
            }
        }

        Ok(())
    }

    /// Cancel the build process
    pub fn cancel_build(&mut self) -> Result<(), String> {
        let mut status = self.status.lock().unwrap();
        if !status.is_running {
            return Err("Build is not running".to_string());
        }

        status.is_running = false;
        status.stage = BuildStage::Cancelled;
        status.end_time = Some(
            SystemTime::now()
                .duration_since(UNIX_EPOCH)
                .unwrap_or_default()
                .as_secs(),
        );

        // Terminate process
        if let Some(mut process) = self.process.take() {
            let _ = process.kill();
        }

        Ok(())
    }

    /// Get current build status
    pub fn get_status(&self) -> BuildStatus {
        self.status.lock().unwrap().clone()
    }

    /// Get build logs
    pub fn get_logs(&self) -> Result<Vec<LogEntry>, String> {
        let mut logs = Vec::new();

        if let Some(log_path) = &self.log_file {
            if let Ok(file) = File::open(log_path) {
                let reader = BufReader::new(file);
                let status = self.status.lock().unwrap();

                for (idx, line) in reader.lines().enumerate() {
                    if let Ok(log_line) = line {
                        let entry = LogEntry {
                            timestamp: status.start_time + (idx as u64),
                            level: Self::detect_log_level(&log_line),
                            message: log_line,
                            stage: status.stage.clone(),
                        };
                        logs.push(entry);
                    }
                }
            }
        }

        Ok(logs)
    }

    /// Detect log level from message
    fn detect_log_level(message: &str) -> String {
        if message.contains("Error") || message.contains("error") {
            "ERROR".to_string()
        } else if message.contains("Warning") || message.contains("warning") {
            "WARN".to_string()
        } else if message.contains("✓") || message.contains("success") {
            "SUCCESS".to_string()
        } else {
            "INFO".to_string()
        }
    }
}
