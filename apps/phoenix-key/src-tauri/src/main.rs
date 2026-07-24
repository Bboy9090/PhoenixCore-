#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use libbootforge::{scan_devices, DeviceInfo};
use serde_json::Value;
use std::{fs, path::PathBuf, process::Command};

const USB_CREATOR_SOURCE: &str = include_str!("../../../../usb_creator.py");
const DEVICE_SCANNER_SOURCE: &str = include_str!("../../../../device_scanner.py");

#[tauri::command]
fn scan_connected_devices() -> Result<Vec<DeviceInfo>, String> {
    scan_devices().map_err(|error| error.to_string())
}

fn bridge_directory() -> Result<PathBuf, String> {
    let directory = std::env::temp_dir().join(format!("phoenix-key-{}", std::process::id()));
    fs::create_dir_all(&directory)
        .map_err(|error| format!("cannot create PhoenixCore bridge directory: {error}"))?;
    fs::write(directory.join("usb_creator.py"), USB_CREATOR_SOURCE)
        .map_err(|error| format!("cannot stage embedded USB creator: {error}"))?;
    fs::write(directory.join("device_scanner.py"), DEVICE_SCANNER_SOURCE)
        .map_err(|error| format!("cannot stage embedded device scanner: {error}"))?;
    Ok(directory)
}

fn run_phoenixcore(args: &[&str]) -> Result<Value, String> {
    let directory = bridge_directory()?;
    let script = directory.join("usb_creator.py");
    let candidates: &[&str] = if cfg!(windows) {
        &["python", "py"]
    } else {
        &["python3", "python"]
    };
    let mut failures = Vec::new();

    for candidate in candidates {
        let mut command = Command::new(candidate);
        if *candidate == "py" {
            command.arg("-3");
        }
        let result = command.arg(&script).args(args).current_dir(&directory).output();
        match result {
            Ok(output) if output.status.success() => {
                let parsed = serde_json::from_slice::<Value>(&output.stdout).map_err(|error| {
                    format!(
                        "PhoenixCore returned invalid JSON: {error}; stdout={}",
                        String::from_utf8_lossy(&output.stdout)
                    )
                });
                let _ = fs::remove_dir_all(&directory);
                return parsed;
            }
            Ok(output) => failures.push(format!(
                "{candidate}: {}",
                String::from_utf8_lossy(&output.stderr).trim()
            )),
            Err(error) => failures.push(format!("{candidate}: {error}")),
        }
    }

    let _ = fs::remove_dir_all(&directory);
    Err(format!(
        "PhoenixCore Python bridge unavailable: {}",
        failures.join(" | ")
    ))
}

fn canonicalize_windows_physical_drive_arg(value: &str) -> String {
    let trimmed = value.trim().replace('/', "\\");
    let upper = trimmed.to_ascii_uppercase();
    let marker = "PHYSICALDRIVE";

    if let Some(index) = upper.find(marker) {
        let suffix = &upper[index + marker.len()..];
        let digits: String = suffix
            .chars()
            .take_while(|character| character.is_ascii_digit())
            .collect();

        if !digits.is_empty() {
            return format!("\\\\.\\PHYSICALDRIVE{digits}");
        }
    }

    trimmed
}

#[tauri::command]
fn scan_media_targets() -> Result<Value, String> {
    run_phoenixcore(&["--list-json"])
}

#[tauri::command]
fn plan_media_build(target_drive: String, image_path: String) -> Result<Value, String> {
    if target_drive.trim().is_empty() || image_path.trim().is_empty() {
        return Err("target drive and image path are required".to_string());
    }

    let normalized_target = canonicalize_windows_physical_drive_arg(&target_drive);
    let normalized_image = image_path.trim().to_string();

    run_phoenixcore(&[
        "--plan-write",
        "--target-drive",
        &normalized_target,
        "--image",
        &normalized_image,
    ])
}

fn main() {
    tauri::Builder::default()
        .invoke_handler(tauri::generate_handler![
            scan_connected_devices,
            scan_media_targets,
            plan_media_build
        ])
        .run(tauri::generate_context!())
        .expect("failed to run Phoenix Key desktop application");
}

#[cfg(test)]
mod tests {
    use super::canonicalize_windows_physical_drive_arg;

    #[test]
    fn canonicalizes_standard_windows_physical_drive() {
        assert_eq!(
            canonicalize_windows_physical_drive_arg(r"\\.\PHYSICALDRIVE1"),
            r"\\.\PHYSICALDRIVE1"
        );
    }

    #[test]
    fn canonicalizes_plain_physical_drive() {
        assert_eq!(
            canonicalize_windows_physical_drive_arg("PHYSICALDRIVE1"),
            r"\\.\PHYSICALDRIVE1"
        );
    }

    #[test]
    fn canonicalizes_lowercase_physical_drive() {
        assert_eq!(
            canonicalize_windows_physical_drive_arg("physicaldrive1"),
            r"\\.\PHYSICALDRIVE1"
        );
    }

    #[test]
    fn canonicalizes_over_escaped_physical_drive() {
        assert_eq!(
            canonicalize_windows_physical_drive_arg(r"\\\\.\\PHYSICALDRIVE1"),
            r"\\.\PHYSICALDRIVE1"
        );
    }

    #[test]
    fn leaves_non_physical_drive_target_unchanged() {
        assert_eq!(canonicalize_windows_physical_drive_arg("E:\\"), "E:\\");
    }
}
