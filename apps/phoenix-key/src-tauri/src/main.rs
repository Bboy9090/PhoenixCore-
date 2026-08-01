#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

mod windows_target;

use libbootforge::{scan_devices, DeviceInfo};
use serde::Serialize;
use serde_json::{json, Value};
use std::{
    ffi::OsStr,
    fs,
    path::{Path, PathBuf},
    process::Command,
};
use windows_target::{resolve_target, TargetResolution};

const USB_CREATOR_SOURCE: &str = include_str!("../../../../usb_creator.py");
const DEVICE_SCANNER_SOURCE: &str = include_str!("../../../../device_scanner.py");
const DRIVE_EVIDENCE_SOURCE: &str =
    include_str!("../../../../scripts/hardware/capture_windows_drive_evidence.py");
const SACRIFICIAL_WRITER_SOURCE: &str =
    include_str!("../../../../scripts/hardware/write_windows_sacrificial_drive.py");
const SMOKE_RECEIPT_ENV: &str = "PHOENIX_KEY_SMOKE_RECEIPT";
const TARGET_RESOLUTION_SCHEMA: &str = "phoenix_key.target_resolution.v1";
const WRITE_UNLOCK_ENV: &str = "BWS_ENABLE_SACRIFICIAL_DRIVE_WRITE";
const WRITE_UNLOCK_VALUE: &str = "I_ACCEPT_COMPLETE_DESTRUCTION_OF_NAMED_TEST_DRIVE";

#[derive(Debug, Serialize)]
struct SmokeSafetyBoundary {
    hardware_scan: &'static str,
    media_plan: &'static str,
    physical_write: &'static str,
    browser_hardware_fabrication: &'static str,
}

#[derive(Debug, Serialize)]
struct InstalledSmokeReceipt {
    schema_version: &'static str,
    app_id: &'static str,
    product_name: &'static str,
    version: &'static str,
    source_commit: &'static str,
    target_os: &'static str,
    target_arch: &'static str,
    process_id: u32,
    mode: &'static str,
    safety_boundary: SmokeSafetyBoundary,
    status: &'static str,
}

fn installed_smoke_receipt(process_id: u32) -> InstalledSmokeReceipt {
    InstalledSmokeReceipt {
        schema_version: "bws.phoenix-key-installed-smoke/v1",
        app_id: "phoenix-usb-creator",
        product_name: "Phoenix Key",
        version: env!("CARGO_PKG_VERSION"),
        source_commit: option_env!("PHOENIX_KEY_SOURCE_COMMIT").unwrap_or("unrecorded"),
        target_os: std::env::consts::OS,
        target_arch: std::env::consts::ARCH,
        process_id,
        mode: "installed-executable-guarded-writer-smoke",
        safety_boundary: SmokeSafetyBoundary {
            hardware_scan: "not-invoked",
            media_plan: "not-invoked",
            physical_write: "guarded-not-invoked",
            browser_hardware_fabrication: "prohibited",
        },
        status: "pass",
    }
}

fn smoke_mode_requested() -> bool {
    std::env::args_os()
        .skip(1)
        .any(|argument| argument == OsStr::new("--smoke-test"))
}

fn write_installed_smoke_receipt(path: &Path) -> Result<(), String> {
    if let Some(parent) = path.parent().filter(|parent| !parent.as_os_str().is_empty()) {
        fs::create_dir_all(parent)
            .map_err(|error| format!("cannot create smoke receipt directory: {error}"))?;
    }

    let receipt = installed_smoke_receipt(std::process::id());
    let payload = serde_json::to_vec_pretty(&receipt)
        .map_err(|error| format!("cannot serialize installed smoke receipt: {error}"))?;
    fs::write(path, payload).map_err(|error| format!("cannot write installed smoke receipt: {error}"))
}

fn run_smoke_mode_if_requested() -> Result<bool, String> {
    if !smoke_mode_requested() {
        return Ok(false);
    }

    let receipt_path = std::env::var_os(SMOKE_RECEIPT_ENV)
        .filter(|value| !value.is_empty())
        .map(PathBuf::from)
        .ok_or_else(|| format!("{SMOKE_RECEIPT_ENV} is required for --smoke-test"))?;

    write_installed_smoke_receipt(&receipt_path)?;
    Ok(true)
}

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
    fs::write(
        directory.join("capture_windows_drive_evidence.py"),
        DRIVE_EVIDENCE_SOURCE,
    )
    .map_err(|error| format!("cannot stage embedded drive evidence collector: {error}"))?;
    fs::write(
        directory.join("write_windows_sacrificial_drive.py"),
        SACRIFICIAL_WRITER_SOURCE,
    )
    .map_err(|error| format!("cannot stage embedded physical writer: {error}"))?;
    Ok(directory)
}

fn python_candidates() -> &'static [&'static str] {
    if cfg!(windows) {
        &["python", "py"]
    } else {
        &["python3", "python"]
    }
}

fn run_python_json(
    script: &Path,
    args: &[&str],
    environment: &[(&str, &str)],
) -> Result<Value, String> {
    let mut failures = Vec::new();
    for candidate in python_candidates() {
        let mut command = Command::new(candidate);
        if *candidate == "py" {
            command.arg("-3");
        }
        command.arg(script).args(args).envs(environment.iter().copied());
        match command.output() {
            Ok(output) if output.status.success() => {
                return serde_json::from_slice::<Value>(&output.stdout).map_err(|error| {
                    format!(
                        "Phoenix Key helper returned invalid JSON: {error}; stdout={}",
                        String::from_utf8_lossy(&output.stdout)
                    )
                });
            }
            Ok(output) => failures.push(format!(
                "{candidate}: {}",
                String::from_utf8_lossy(&output.stderr).trim()
            )),
            Err(error) => failures.push(format!("{candidate}: {error}")),
        }
    }
    Err(format!(
        "Phoenix Key Python helper unavailable: {}",
        failures.join(" | ")
    ))
}

fn run_phoenixcore(args: &[&str]) -> Result<Value, String> {
    let directory = bridge_directory()?;
    let script = directory.join("usb_creator.py");
    let result = run_python_json(&script, args, &[]);
    let _ = fs::remove_dir_all(&directory);
    result
}

fn source_commit() -> Result<&'static str, String> {
    let commit = option_env!("PHOENIX_KEY_SOURCE_COMMIT").unwrap_or("");
    if commit.len() == 40
        && commit
            .bytes()
            .all(|byte| byte.is_ascii_digit() || (b'a'..=b'f').contains(&byte))
    {
        Ok(commit)
    } else {
        Err("this Phoenix Key build lacks a valid 40-character source commit".to_string())
    }
}

fn expected_authorization(target: &str, identity: &str, size: u64) -> String {
    format!(
        "I AUTHORIZE COMPLETE DESTRUCTION OF {} IDENTITY {} SIZE {}",
        target.to_uppercase(),
        identity,
        size
    )
}

fn require_write_candidate(evidence: &Value) -> Result<(&str, &str, u64), String> {
    let disk = evidence
        .get("disk")
        .ok_or_else(|| "drive evidence is missing its disk record".to_string())?;
    if disk.get("write_candidate").and_then(Value::as_bool) != Some(true) {
        return Err(format!(
            "target is not a safe write candidate: {}",
            disk.get("write_block_reasons")
                .cloned()
                .unwrap_or(Value::Null)
        ));
    }
    let target = disk
        .get("target")
        .and_then(Value::as_str)
        .ok_or_else(|| "drive evidence is missing the canonical target".to_string())?;
    let identity = disk
        .get("identity_sha256")
        .and_then(Value::as_str)
        .ok_or_else(|| "drive evidence is missing its stable identity".to_string())?;
    if identity.len() != 64 || !identity.bytes().all(|byte| byte.is_ascii_hexdigit()) {
        return Err("drive evidence contains an invalid identity SHA-256".to_string());
    }
    let size = disk
        .get("size_bytes")
        .and_then(Value::as_u64)
        .ok_or_else(|| "drive evidence is missing its capacity".to_string())?;
    Ok((target, identity, size))
}

fn capture_write_evidence(directory: &Path, target: &str, name: &str) -> Result<Value, String> {
    if !cfg!(windows) {
        return Err("physical media writing is supported only on Windows".to_string());
    }
    let script = directory.join("capture_windows_drive_evidence.py");
    let output = directory.join(name);
    let output_text = output.to_string_lossy().to_string();
    run_python_json(
        &script,
        &[
            "--target",
            target,
            "--output",
            &output_text,
            "--source-commit",
            source_commit()?,
        ],
        &[],
    )
}

fn receipt_directory() -> Result<PathBuf, String> {
    let base = std::env::var_os("LOCALAPPDATA")
        .map(PathBuf::from)
        .unwrap_or_else(std::env::temp_dir);
    let directory = base.join("PhoenixKey").join("receipts");
    fs::create_dir_all(&directory)
        .map_err(|error| format!("cannot create Phoenix Key receipt directory: {error}"))?;
    Ok(directory)
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

    let resolution_status = if resolution.is_windows_physical_drive() {
        if scanner_planner_consistent {
            "target_resolved_from_scanner_evidence"
        } else {
            "target_not_resolved_from_scanner_evidence"
        }
    } else {
        "target_passthrough"
    };

    let object = plan
        .as_object_mut()
        .ok_or_else(|| "phoenixcore_plan_not_json_object".to_string())?;

    object.insert(
        "target_resolution".to_string(),
        json!({
            "schema": TARGET_RESOLUTION_SCHEMA,
            "requested_path": &resolution.requested_path,
            "canonical_path": &resolution.canonical_path,
            "resolution_source": resolution.resolution_source,
            "resolution_status": resolution_status,
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

#[tauri::command]
fn prepare_media_write(target_drive: String, image_path: String) -> Result<Value, String> {
    if target_drive.trim().is_empty() || image_path.trim().is_empty() {
        return Err("target drive and image path are required".to_string());
    }
    let resolution = resolve_target(&target_drive)?;
    if !resolution.is_windows_physical_drive() {
        return Err("write target must be an exact Windows PHYSICALDRIVE path".to_string());
    }
    let image = PathBuf::from(image_path.trim());
    if !image.is_file() {
        return Err("source image does not exist or is not a regular file".to_string());
    }

    let directory = bridge_directory()?;
    let result = (|| {
        let evidence = capture_write_evidence(
            &directory,
            &resolution.canonical_path,
            "phoenix-key-prewrite-evidence.json",
        )?;
        let (target, identity, size) = require_write_candidate(&evidence)?;
        let image_size = image
            .metadata()
            .map_err(|error| format!("cannot inspect source image: {error}"))?
            .len();
        if image_size == 0 {
            return Err("source image is empty".to_string());
        }
        if image_size > size {
            return Err("source image is larger than the selected target".to_string());
        }
        Ok(json!({
            "schema": "phoenix_key.write_preparation.v1",
            "target": target,
            "target_identity_sha256": identity,
            "target_size_bytes": size,
            "image_path": image.to_string_lossy(),
            "image_size_bytes": image_size,
            "authorization_phrase": expected_authorization(target, identity, size),
            "write_candidate": true,
            "physical_write_attempted": false,
            "bytes_written": 0
        }))
    })();
    let _ = fs::remove_dir_all(&directory);
    result
}

#[tauri::command]
fn execute_media_write(
    target_drive: String,
    image_path: String,
    authorization: String,
    destructive_acknowledgement: bool,
) -> Result<Value, String> {
    if !destructive_acknowledgement {
        return Err("destructive acknowledgement is required".to_string());
    }
    let resolution = resolve_target(&target_drive)?;
    if !resolution.is_windows_physical_drive() {
        return Err("write target must be an exact Windows PHYSICALDRIVE path".to_string());
    }
    let image = PathBuf::from(image_path.trim());
    if !image.is_file() {
        return Err("source image does not exist or is not a regular file".to_string());
    }

    let directory = bridge_directory()?;
    let result = (|| {
        let evidence = capture_write_evidence(
            &directory,
            &resolution.canonical_path,
            "phoenix-key-write-evidence.json",
        )?;
        let (target, identity, size) = require_write_candidate(&evidence)?;
        let required = expected_authorization(target, identity, size);
        if authorization != required {
            return Err("authorization phrase does not match the freshly scanned target".to_string());
        }

        let script = directory.join("write_windows_sacrificial_drive.py");
        let evidence_path = directory.join("phoenix-key-write-evidence.json");
        let receipt_path = receipt_directory()?.join(format!(
            "phoenix-key-write-receipt-{}-{}.json",
            std::process::id(),
            &identity[..12]
        ));
        let evidence_text = evidence_path.to_string_lossy().to_string();
        let image_text = image.to_string_lossy().to_string();
        let receipt_text = receipt_path.to_string_lossy().to_string();
        let mut receipt = run_python_json(
            &script,
            &[
                "--drive-receipt",
                &evidence_text,
                "--image",
                &image_text,
                "--target",
                target,
                "--authorization",
                &authorization,
                "--source-commit",
                source_commit()?,
                "--output",
                &receipt_text,
                "--execute",
            ],
            &[(WRITE_UNLOCK_ENV, WRITE_UNLOCK_VALUE)],
        )?;
        let object = receipt
            .as_object_mut()
            .ok_or_else(|| "writer receipt is not a JSON object".to_string())?;
        object.insert(
            "receipt_path".to_string(),
            Value::String(receipt_text),
        );
        Ok(receipt)
    })();
    let _ = fs::remove_dir_all(&directory);
    result
}

fn main() {
    match run_smoke_mode_if_requested() {
        Ok(true) => return,
        Ok(false) => {}
        Err(_) => std::process::exit(70),
    }

    tauri::Builder::default()
        .invoke_handler(tauri::generate_handler![
            scan_connected_devices,
            scan_media_targets,
            plan_media_build,
            prepare_media_write,
            execute_media_write
        ])
        .run(tauri::generate_context!())
        .expect("failed to run Phoenix Key desktop application");
}

#[cfg(test)]
mod tests {
    use super::{
        attach_target_resolution, expected_authorization, installed_smoke_receipt,
        require_write_candidate, resolve_target,
    };
    use serde_json::json;

    #[test]
    fn installed_smoke_receipt_is_read_only_and_non_destructive() {
        let receipt = installed_smoke_receipt(42);
        let value = serde_json::to_value(receipt).expect("smoke receipt should serialize");

        assert_eq!(value["schema_version"], "bws.phoenix-key-installed-smoke/v1");
        assert_eq!(value["app_id"], "phoenix-usb-creator");
        assert_eq!(value["process_id"], 42);
        assert_eq!(value["status"], "pass");
        assert_eq!(value["safety_boundary"]["hardware_scan"], "not-invoked");
        assert_eq!(value["safety_boundary"]["media_plan"], "not-invoked");
        assert_eq!(
            value["safety_boundary"]["physical_write"],
            "guarded-not-invoked"
        );
        assert_eq!(
            value["safety_boundary"]["browser_hardware_fabrication"],
            "prohibited"
        );
    }

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
            plan.pointer("/target_resolution/schema")
                .and_then(|value| value.as_str()),
            Some("phoenix_key.target_resolution.v1")
        );
        assert_eq!(
            plan.pointer("/target_resolution/canonical_path")
                .and_then(|value| value.as_str()),
            Some(r"\\.\PHYSICALDRIVE1")
        );
        assert_eq!(
            plan.pointer("/target_resolution/resolution_status")
                .and_then(|value| value.as_str()),
            Some("target_resolved_from_scanner_evidence")
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
            plan.pointer("/target_resolution/resolution_status")
                .and_then(|value| value.as_str()),
            Some("target_not_resolved_from_scanner_evidence")
        );
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
    fn records_passthrough_target_status() {
        let resolution = resolve_target("E:\\").unwrap();
        let mut plan = json!({
            "drive_safety": {
                "drive": {
                    "root": "E:\\"
                }
            }
        });

        attach_target_resolution(&mut plan, &resolution).unwrap();

        assert_eq!(
            plan.pointer("/target_resolution/resolution_status")
                .and_then(|value| value.as_str()),
            Some("target_passthrough")
        );
        assert_eq!(
            plan.pointer("/target_resolution/scanner_planner_consistent")
                .and_then(|value| value.as_bool()),
            Some(true)
        );
    }

    #[test]
    fn rejects_non_object_plan_payload() {
        let resolution = resolve_target("PHYSICALDRIVE1").unwrap();
        let mut plan = json!(["unexpected"]);

        let error = attach_target_resolution(&mut plan, &resolution).unwrap_err();
        assert_eq!(error, "phoenixcore_plan_not_json_object");
    }

    #[test]
    fn authorization_binds_target_identity_and_capacity() {
        assert_eq!(
            expected_authorization(r"\\.\physicaldrive7", "abc123", 4096),
            r"I AUTHORIZE COMPLETE DESTRUCTION OF \\.\PHYSICALDRIVE7 IDENTITY abc123 SIZE 4096"
        );
    }

    #[test]
    fn accepts_only_positive_safe_device_evidence() {
        let evidence = json!({
            "disk": {
                "target": r"\\.\PHYSICALDRIVE7",
                "identity_sha256": "a".repeat(64),
                "size_bytes": 8192,
                "write_candidate": true,
                "write_block_reasons": []
            }
        });
        let (target, identity, size) = require_write_candidate(&evidence).unwrap();
        assert_eq!(target, r"\\.\PHYSICALDRIVE7");
        assert_eq!(identity, "a".repeat(64));
        assert_eq!(size, 8192);
    }

    #[test]
    fn rejects_blocked_or_ambiguous_device_evidence() {
        let evidence = json!({
            "disk": {
                "target": r"\\.\PHYSICALDRIVE0",
                "identity_sha256": "b".repeat(64),
                "size_bytes": 8192,
                "write_candidate": false,
                "write_block_reasons": ["target-is-system-disk"]
            }
        });
        let error = require_write_candidate(&evidence).unwrap_err();
        assert!(error.contains("target-is-system-disk"));
    }
}
