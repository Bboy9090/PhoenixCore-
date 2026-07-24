#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

mod windows_target;

use libbootforge::{scan_devices, DeviceInfo};
use serde_json::{json, Value};
use std::{fs, path::PathBuf, process::Command};
use windows_target::{resolve_target, TargetResolution};

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

fn attach_target_resolution(
    plan: &mut Value,
    resolution: &TargetResolution,
) -> Result<(), String> {
    let planner_root = plan
        .pointer("/drive_safety/drive/root")
        .and_then(Value::as_str)
        .map(str::to_string);

    let scanner_planner_consistent = if resolution.is_windows_physical_drive() {
        planner_root
            .as_deref()
            .map(|root| root.eq_ignore_ascii_case(&resolution.canonical_path))
            .unwrap_or(false)
    } else {
        true
    };

    let object = plan
        .as_object_mut()
        .ok_or_else(|| "phoenixcore_plan_not_json_object".to_string())?;

    object.insert(
        "target_resolution".to_string(),
        json!({
            "requested_path": resolution.requested_path,
            "canonical_path": resolution.canonical_path,
            "resolution_source": resolution.resolution_source,
            "target_kind": resolution.target_kind,
            "canonicalized": resolution.canonicalized,
            "planner_root": planner_root,
            "scanner_planner_consistent": scanner_planner_consistent,
        }),
    );

    Ok(())
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

    let target_resolution = resolve_target(&target_drive)?;
    let normalized_image = image_path.trim().to_string();

    let mut plan = run_phoenixcore(&[
        "--plan-write",
        "--target-drive",
        &target_resolution.canonical_path,
        "--image",
        &normalized_image,
    ])?;
    attach_target_resolution(&mut plan, &target_resolution)?;
    Ok(plan)
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
    use super::{attach_target_resolution, resolve_target};
    use serde_json::json;

    #[test]
    fn records_consistent_scanner_planner_resolution() {
        let resolution = resolve_target("PHYSICALDRIVE1").unwrap();
        let mut plan = json!({
            "drive_safety": {
                "drive": {
                    "root": "\\\\.\\PHYSICALDRIVE1"
                }
            }
        });

        attach_target_resolution(&mut plan, &resolution).unwrap();

        assert_eq!(
            plan.pointer("/target_resolution/canonical_path")
                .and_then(|value| value.as_str()),
            Some(r"\\.\PHYSICALDRIVE1")
        );
        assert_eq!(
            plan.pointer("/target_resolution/scanner_planner_consistent")
                .and_then(|value| value.as_bool()),
            Some(true)
        );
    }

    #[test]
    fn records_missing_planner_root_as_inconsistent() {
        let resolution = resolve_target("PHYSICALDRIVE1").unwrap();
        let mut plan = json!({
            "blocked": true,
            "block_reasons": ["target_not_found_in_scan_evidence"]
        });

        attach_target_resolution(&mut plan, &resolution).unwrap();

        assert_eq!(
            plan.pointer("/target_resolution/scanner_planner_consistent")
                .and_then(|value| value.as_bool()),
            Some(false)
        );
        assert!(plan
            .pointer("/target_resolution/planner_root")
            .is_some_and(|value| value.is_null()));
    }

    #[test]
    fn rejects_non_object_plan_payload() {
        let resolution = resolve_target("PHYSICALDRIVE1").unwrap();
        let mut plan = json!(["unexpected"]);

        let error = attach_target_resolution(&mut plan, &resolution).unwrap_err();
        assert_eq!(error, "phoenixcore_plan_not_json_object");
    }
}
