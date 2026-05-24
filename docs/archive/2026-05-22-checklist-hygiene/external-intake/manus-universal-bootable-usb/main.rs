// Tauri backend for Phoenix Control Center
// 
// Provides system monitoring and management commands

#![cfg_attr(all(not(debug_assertions), target_os = "windows"), windows_subsystem = "windows")]

mod system;
mod build_monitor;
mod notifications;
mod log_export;

use tauri::Manager;
use system::*;
use build_monitor::*;
use notifications::NotificationManager;
use log_export::{LogExporter, ExportResult};
use std::sync::{Arc, Mutex};

/// Get system information
#[tauri::command]
async fn get_system_info() -> Result<SystemInfo, String> {
    system::get_system_info()
}

/// Get CPU usage percentage
#[tauri::command]
async fn get_cpu_usage() -> Result<f32, String> {
    system::get_cpu_usage()
}

/// Get memory usage percentage
#[tauri::command]
async fn get_memory_usage() -> Result<f32, String> {
    system::get_memory_usage()
}

/// Get disk information
#[tauri::command]
async fn get_disk_info() -> Result<Vec<DiskInfo>, String> {
    system::get_disk_info()
}

/// Get running processes
#[tauri::command]
async fn get_processes() -> Result<Vec<ProcessInfo>, String> {
    system::get_processes()
}

/// Get network interfaces
#[tauri::command]
async fn get_network_interfaces() -> Result<Vec<NetworkInterface>, String> {
    system::get_network_interfaces()
}

/// Get hardware information
#[tauri::command]
async fn get_hardware_info() -> Result<HardwareInfo, String> {
    system::get_hardware_info()
}

/// Get partition information with safety checks
#[tauri::command]
async fn get_partitions() -> Result<Vec<PartitionInfo>, String> {
    system::get_partitions()
}

/// Scan disk for errors (with safety checks)
#[tauri::command]
async fn scan_disk_errors(device: String) -> Result<ScanResult, String> {
    system::scan_disk_errors(&device)
}

/// Repair disk (with safety checks)
#[tauri::command]
async fn repair_disk(device: String) -> Result<RepairResult, String> {
    system::repair_disk(&device)
}

/// Clear system cache
#[tauri::command]
async fn clear_system_cache() -> Result<CacheResult, String> {
    system::clear_system_cache()
}

/// Get system logs
#[tauri::command]
async fn get_system_logs(lines: usize) -> Result<Vec<String>, String> {
    system::get_system_logs(lines)
}

/// Start Phoenix OS build
#[tauri::command]
async fn start_phoenix_build(
    build_dir: String,
    state: tauri::State<'_, Arc<Mutex<BuildManager>>>,
) -> Result<BuildStatus, String> {
    let mut manager = state.lock().unwrap();
    manager.start_build(std::path::PathBuf::from(build_dir))?;
    Ok(manager.get_status())
}

/// Get build status
#[tauri::command]
async fn get_build_status(state: tauri::State<'_, Arc<Mutex<BuildManager>>>) -> BuildStatus {
    let manager = state.lock().unwrap();
    manager.get_status()
}

/// Pause build
#[tauri::command]
async fn pause_build(state: tauri::State<'_, Arc<Mutex<BuildManager>>>) -> Result<(), String> {
    let mut manager = state.lock().unwrap();
    manager.pause_build()
}

/// Resume build
#[tauri::command]
async fn resume_build(state: tauri::State<'_, Arc<Mutex<BuildManager>>>) -> Result<(), String> {
    let mut manager = state.lock().unwrap();
    manager.resume_build()
}

/// Cancel build
#[tauri::command]
async fn cancel_build(state: tauri::State<'_, Arc<Mutex<BuildManager>>>) -> Result<(), String> {
    let mut manager = state.lock().unwrap();
    manager.cancel_build()
}

/// Get build logs
#[tauri::command]
async fn get_build_logs(
    state: tauri::State<'_, Arc<Mutex<BuildManager>>>,
) -> Result<Vec<LogEntry>, String> {
    let manager = state.lock().unwrap();
    manager.get_logs()
}

/// Notify build success
#[tauri::command]
async fn notify_build_success(iso_path: String, iso_size: u64) -> Result<(), String> {
    NotificationManager::notify_build_success(&iso_path, iso_size)
}

/// Notify build failed
#[tauri::command]
async fn notify_build_failed(error: String) -> Result<(), String> {
    NotificationManager::notify_build_failed(&error)
}

/// Notify build paused
#[tauri::command]
async fn notify_build_paused(stage: String, progress: u32) -> Result<(), String> {
    NotificationManager::notify_build_paused(&stage, progress)
}

/// Notify build resumed
#[tauri::command]
async fn notify_build_resumed(stage: String) -> Result<(), String> {
    NotificationManager::notify_build_resumed(&stage)
}

/// Notify build cancelled
#[tauri::command]
async fn notify_build_cancelled() -> Result<(), String> {
    NotificationManager::notify_build_cancelled()
}

/// Notify system warning
#[tauri::command]
async fn notify_system_warning(warning: String) -> Result<(), String> {
    NotificationManager::notify_system_warning(&warning)
}

/// Notify system error
#[tauri::command]
async fn notify_system_error(error: String) -> Result<(), String> {
    NotificationManager::notify_system_error(&error)
}

/// Export build logs to text file
#[tauri::command]
async fn export_logs_to_text(
    logs: Vec<log_export::LogEntry>,
    output_path: Option<String>,
) -> Result<ExportResult, String> {
    LogExporter::export_to_text(logs, output_path)
}

/// Export build logs to JSON file
#[tauri::command]
async fn export_logs_to_json(
    logs: Vec<log_export::LogEntry>,
    output_path: Option<String>,
) -> Result<ExportResult, String> {
    LogExporter::export_to_json(logs, output_path)
}

/// Export build logs to CSV file
#[tauri::command]
async fn export_logs_to_csv(
    logs: Vec<log_export::LogEntry>,
    output_path: Option<String>,
) -> Result<ExportResult, String> {
    LogExporter::export_to_csv(logs, output_path)
}

/// Get default export directory
#[tauri::command]
async fn get_export_directory() -> Result<String, String> {
    LogExporter::get_export_directory()
        .map(|p| p.to_string_lossy().to_string())
}

fn main() {
    tauri::Builder::default()
        .manage(Arc::new(Mutex::new(BuildManager::new())))
        .invoke_handler(tauri::generate_handler![
            get_system_info,
            get_cpu_usage,
            get_memory_usage,
            get_disk_info,
            get_processes,
            get_network_interfaces,
            get_hardware_info,
            get_partitions,
            scan_disk_errors,
            repair_disk,
            clear_system_cache,
            get_system_logs,
            start_phoenix_build,
            get_build_status,
            pause_build,
            resume_build,
            cancel_build,
            get_build_logs,
            notify_build_success,
            notify_build_failed,
            notify_build_paused,
            notify_build_resumed,
            notify_build_cancelled,
            notify_system_warning,
            notify_system_error,
            export_logs_to_text,
            export_logs_to_json,
            export_logs_to_csv,
            get_export_directory,
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
