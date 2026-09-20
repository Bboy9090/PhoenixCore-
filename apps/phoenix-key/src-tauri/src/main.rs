#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

mod boot_repair_contract;
mod data_preservation;
mod intel_mac_restore_gate;
mod mac_bootcamp_compat;
mod recovery_center;
mod recovery_evidence_bundle;
mod restore_preflight;
mod rollback_destination;
mod restore_readiness;
mod restore_rollback_contract;
mod source_identity;
mod target_reenumeration;
mod target_safety;
mod windows_recovery;
mod windows_recovery_guard;
mod windows_target;

use boot_repair_contract::plan_windows_boot_repair;
use data_preservation::create_target_data_preservation_decision;
use intel_mac_restore_gate::assess_intel_mac_restore_readiness;
use mac_bootcamp_compat::inspect_mac_bootcamp_host;
use libbootforge::{scan_devices, DeviceFamily, DeviceInfo, DeviceMode};
use restore_preflight::assess_windows_restore_hardware_preflight;
use restore_readiness::assess_windows_restore_readiness;
use restore_rollback_contract::{
    plan_restore_target_rollback_contract, verify_restore_target_rollback_contract_sha256,
};
use rollback_destination::{assess_rollback_destination, RollbackDestinationVerification};
use recovery_center::{
    analyze_windows_recovery_source, plan_windows_recovery_source,
    verify_windows_recovery_source_identity,
};
use recovery_evidence_bundle::build_windows_recovery_evidence_bundle_v2;
use serde::Serialize;
use serde_json::{json, Value};
use source_identity::capture_source_identity;
use target_reenumeration::{
    compare_recovery_target_reenumeration,
};
use target_safety::{
    assess_recovery_target, verify_recovery_target_identity,
    RecoveryTargetIdentityVerification, RecoveryTargetSafety,
};
use std::{
    ffi::OsStr,
    fs,
    path::{Path, PathBuf},
    process::Command,
};
use windows_target::{resolve_target, TargetResolution};

#[cfg(not(feature = "store-safe"))]
const USB_CREATOR_SOURCE: &str = include_str!("../../../../usb_creator.py");
#[cfg(not(feature = "store-safe"))]
const DEVICE_SCANNER_SOURCE: &str = include_str!("../../../../device_scanner.py");
#[cfg(not(feature = "store-safe"))]
const DRIVE_EVIDENCE_SOURCE: &str =
    include_str!("../../../../scripts/hardware/capture_windows_drive_evidence.py");
#[cfg(not(feature = "store-safe"))]
const STABLE_TARGET_LOCATOR_SOURCE: &str =
    include_str!("../../../../scripts/hardware/find_windows_drive_by_stable_identity.py");
#[cfg(not(feature = "store-safe"))]
const SOURCE_DISK_RESOLVER_SOURCE: &str =
    include_str!("../../../../scripts/hardware/resolve_windows_source_disk.py");
#[cfg(not(feature = "store-safe"))]
const PACKAGE_TRUST_INSPECTOR_SOURCE: &str =
    include_str!("../../../../scripts/hardware/inspect_recovery_package_trust.py");
#[cfg(not(feature = "store-safe"))]
const CLOUD_STAGE_SOURCE: &str =
    include_str!("../../../../scripts/hardware/stage_cloud_recovery_payload.py");
#[cfg(not(feature = "store-safe"))]
const GOOGLE_DRIVE_ACQUISITION_SOURCE: &str =
    include_str!("../../../../scripts/hardware/acquire_google_drive_recovery.py");
#[cfg(not(feature = "store-safe"))]
const GOOGLE_DRIVE_PICKER_SOURCE: &str =
    include_str!("../../../../scripts/hardware/google_drive_picker_recovery.py");
#[cfg(not(feature = "store-safe"))]
const FAT32_WINDOWS_MEDIA_PLANNER_SOURCE: &str =
    include_str!("../../../../scripts/hardware/plan_fat32_windows_media.py");
#[cfg(not(feature = "store-safe"))]
const WINDOWS_IMAGE_METADATA_SOURCE: &str =
    include_str!("../../../../scripts/hardware/inspect_windows_image_metadata.py");
#[cfg(not(feature = "store-safe"))]
const BOOTCAMP_DRIVER_INSPECTOR_SOURCE: &str =
    include_str!("../../../../scripts/hardware/inspect_bootcamp_driver_package.py");
#[cfg(not(feature = "store-safe"))]
const WINDOWS_BOOT_STATE_SOURCE: &str =
    include_str!("../../../../scripts/hardware/capture_windows_boot_state.py");
#[cfg(not(feature = "store-safe"))]
const WINDOWS_ROLLBACK_BUNDLE_SOURCE: &str =
    include_str!("../../../../scripts/hardware/persist_windows_rollback_bundle.py");
#[cfg(not(feature = "store-safe"))]
const RESTORE_ROLLBACK_CAPTURE_SOURCE: &str =
    include_str!("../../../../scripts/hardware/capture_windows_restore_rollback.py");
#[cfg(not(feature = "store-safe"))]
const RESTORE_TARGET_BOOT_METADATA_SOURCE: &str =
    include_str!("../../../../scripts/hardware/capture_windows_restore_target_boot_metadata.py");
#[cfg(not(feature = "store-safe"))]
const SACRIFICIAL_WRITER_SOURCE: &str =
    include_str!("../../../../scripts/hardware/write_windows_sacrificial_drive.py");
const SMOKE_RECEIPT_ENV: &str = "PHOENIX_KEY_SMOKE_RECEIPT";
const TARGET_RESOLUTION_SCHEMA: &str = "phoenix_key.target_resolution.v1";
const WRITE_UNLOCK_ENV: &str = "BWS_ENABLE_SACRIFICIAL_DRIVE_WRITE";
const WRITE_UNLOCK_VALUE: &str = "I_ACCEPT_COMPLETE_DESTRUCTION_OF_NAMED_TEST_DRIVE";
const GOOGLE_DRIVE_CLIENT_ID_ENV: &str = "PHOENIX_KEY_GOOGLE_DRIVE_CLIENT_ID";
const GOOGLE_DRIVE_FILE_SCOPE: &str = "https://www.googleapis.com/auth/drive.file";
const STORE_SAFE_DISTRIBUTION: bool = cfg!(feature = "store-safe");

#[derive(Debug, Serialize)]
struct DistributionProfile {
    schema: &'static str,
    channel: &'static str,
    store_safe: bool,
    hardware_scan: bool,
    media_planning: bool,
    physical_media_write: bool,
    external_helper_execution: bool,
    cloud_acquisition: bool,
    native_recovery_analysis: bool,
}

fn current_distribution_profile() -> DistributionProfile {
    if STORE_SAFE_DISTRIBUTION {
        DistributionProfile {
            schema: "phoenix_key.distribution_profile.v1",
            channel: "store-safe",
            store_safe: true,
            hardware_scan: false,
            media_planning: false,
            physical_media_write: false,
            external_helper_execution: false,
            cloud_acquisition: false,
            native_recovery_analysis: true,
        }
    } else {
        DistributionProfile {
            schema: "phoenix_key.distribution_profile.v1",
            channel: "direct",
            store_safe: false,
            hardware_scan: true,
            media_planning: true,
            physical_media_write: true,
            external_helper_execution: true,
            cloud_acquisition: true,
            native_recovery_analysis: true,
        }
    }
}

#[tauri::command]
fn distribution_profile() -> DistributionProfile {
    current_distribution_profile()
}

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
    if STORE_SAFE_DISTRIBUTION {
        return Err("hardware scanning is disabled in the store-safe distribution".to_string());
    }
    scan_devices()
        .map(|devices| {
            devices
                .into_iter()
                .filter(is_actionable_device)
                .collect()
        })
        .map_err(|error| error.to_string())
}

fn is_actionable_device(device: &DeviceInfo) -> bool {
    matches!(
        device.mode,
        DeviceMode::Recovery
            | DeviceMode::Dfu
            | DeviceMode::Bootloader
            | DeviceMode::Fastboot
            | DeviceMode::Adb
    ) || matches!(
        device.fingerprint.family,
        DeviceFamily::IPhone
            | DeviceFamily::IPad
            | DeviceFamily::AndroidPhone
            | DeviceFamily::AndroidTablet
    )
}

#[cfg(feature = "store-safe")]
fn bridge_directory() -> Result<PathBuf, String> {
    Err("external helper execution is disabled in the store-safe distribution".to_string())
}

#[cfg(not(feature = "store-safe"))]
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
        directory.join("find_windows_drive_by_stable_identity.py"),
        STABLE_TARGET_LOCATOR_SOURCE,
    )
    .map_err(|error| format!("cannot stage embedded stable-target locator: {error}"))?;
    fs::write(
        directory.join("resolve_windows_source_disk.py"),
        SOURCE_DISK_RESOLVER_SOURCE,
    )
    .map_err(|error| format!("cannot stage embedded source-disk resolver: {error}"))?;
    fs::write(
        directory.join("inspect_recovery_package_trust.py"),
        PACKAGE_TRUST_INSPECTOR_SOURCE,
    )
    .map_err(|error| format!("cannot stage embedded package trust inspector: {error}"))?;
    fs::write(
        directory.join("stage_cloud_recovery_payload.py"),
        CLOUD_STAGE_SOURCE,
    )
    .map_err(|error| format!("cannot stage embedded cloud staging helper: {error}"))?;
    fs::write(
        directory.join("acquire_google_drive_recovery.py"),
        GOOGLE_DRIVE_ACQUISITION_SOURCE,
    )
    .map_err(|error| format!("cannot stage embedded Drive acquisition helper: {error}"))?;
    fs::write(
        directory.join("google_drive_picker_recovery.py"),
        GOOGLE_DRIVE_PICKER_SOURCE,
    )
    .map_err(|error| format!("cannot stage embedded Google Picker helper: {error}"))?;
    fs::write(
        directory.join("plan_fat32_windows_media.py"),
        FAT32_WINDOWS_MEDIA_PLANNER_SOURCE,
    )
    .map_err(|error| format!("cannot stage embedded FAT32 media planner: {error}"))?;
    fs::write(
        directory.join("inspect_windows_image_metadata.py"),
        WINDOWS_IMAGE_METADATA_SOURCE,
    )
    .map_err(|error| format!("cannot stage embedded Windows image metadata inspector: {error}"))?;
    fs::write(
        directory.join("inspect_bootcamp_driver_package.py"),
        BOOTCAMP_DRIVER_INSPECTOR_SOURCE,
    )
    .map_err(|error| format!("cannot stage embedded Boot Camp driver inspector: {error}"))?;
    fs::write(
        directory.join("capture_windows_boot_state.py"),
        WINDOWS_BOOT_STATE_SOURCE,
    )
    .map_err(|error| format!("cannot stage embedded Windows boot-state collector: {error}"))?;
    fs::write(
        directory.join("persist_windows_rollback_bundle.py"),
        WINDOWS_ROLLBACK_BUNDLE_SOURCE,
    )
    .map_err(|error| format!("cannot stage embedded rollback-bundle helper: {error}"))?;
    fs::write(
        directory.join("capture_windows_restore_rollback.py"),
        RESTORE_ROLLBACK_CAPTURE_SOURCE,
    )
    .map_err(|error| format!("cannot stage embedded restore rollback-capture helper: {error}"))?;
    fs::write(
        directory.join("capture_windows_restore_target_boot_metadata.py"),
        RESTORE_TARGET_BOOT_METADATA_SOURCE,
    )
    .map_err(|error| format!("cannot stage embedded restore target boot-metadata helper: {error}"))?;
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

fn expected_authorization(
    target: &str,
    identity: &str,
    size: u64,
    source_sha256: &str,
) -> String {
    format!(
        "I AUTHORIZE COMPLETE DESTRUCTION OF {} IDENTITY {} SIZE {} SOURCE_SHA256 {}",
        target.to_uppercase(),
        identity,
        size,
        source_sha256
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
fn capture_windows_recovery_baseline(
    source_path: String,
    target_drive: String,
) -> Result<Value, String> {
    if !cfg!(windows) {
        return Err("Windows boot-state capture requires Windows".to_string());
    }
    let source = PathBuf::from(source_path.trim());
    if !source.exists() {
        return Err("recovery source does not exist".to_string());
    }
    let identity = capture_source_identity(&source)?;
    if !identity.complete {
        return Err("recovery source identity is incomplete".to_string());
    }
    let resolution = resolve_target(&target_drive)?;
    if !resolution.is_windows_physical_drive() {
        return Err("rollback target must resolve to an exact Windows PHYSICALDRIVE".to_string());
    }

    let evidence_root = receipt_directory()?.join(format!(
        "recovery-baseline-{}-{}",
        std::process::id(),
        &identity.sha256[..12]
    ));
    fs::create_dir_all(&evidence_root)
        .map_err(|error| format!("cannot create recovery baseline directory: {error}"))?;

    let directory = bridge_directory()?;
    let result = (|| {
        let drive_script = directory.join("capture_windows_drive_evidence.py");
        let drive_receipt = evidence_root.join("drive-evidence.json");
        let drive_receipt_text = drive_receipt.to_string_lossy().to_string();
        let _drive_evidence = run_python_json(
            &drive_script,
            &[
                "--target",
                &resolution.canonical_path,
                "--output",
                &drive_receipt_text,
                "--source-commit",
                source_commit()?,
            ],
            &[],
        )?;

        let boot_script = directory.join("capture_windows_boot_state.py");
        let boot_state = evidence_root.join("boot-state.json");
        let rollback_manifest = evidence_root.join("rollback-manifest.json");
        let source_text = source.to_string_lossy().to_string();
        let boot_state_text = boot_state.to_string_lossy().to_string();
        let rollback_text = rollback_manifest.to_string_lossy().to_string();
        let rollback = run_python_json(
            &boot_script,
            &[
                "--source-identity-sha256",
                &identity.sha256,
                "--source-path",
                &source_text,
                "--drive-receipt",
                &drive_receipt_text,
                "--boot-state-output",
                &boot_state_text,
                "--rollback-output",
                &rollback_text,
            ],
            &[],
        )?;
        let boot: Value = serde_json::from_slice(
            &fs::read(&boot_state)
                .map_err(|error| format!("cannot read persisted boot-state evidence: {error}"))?,
        )
        .map_err(|error| format!("persisted boot-state evidence is invalid JSON: {error}"))?;

        Ok(json!({
            "schema": "phoenix_key.recovery_baseline.v1",
            "source_identity": identity,
            "target": resolution.canonical_path,
            "drive_evidence_path": drive_receipt_text,
            "boot_state_path": boot_state_text,
            "rollback_manifest_path": rollback_text,
            "boot_state": boot,
            "rollback_manifest": rollback,
            "system_mutations_performed": false
        }))
    })();
    let _ = fs::remove_dir_all(&directory);
    result
}

#[tauri::command]
fn persist_windows_recovery_rollback_bundle(
    boot_state_path: String,
    rollback_manifest_path: String,
) -> Result<Value, String> {
    if !cfg!(windows) {
        return Err("Windows rollback bundle persistence requires Windows".to_string());
    }
    let boot_state = PathBuf::from(boot_state_path.trim());
    let rollback_manifest = PathBuf::from(rollback_manifest_path.trim());
    if !boot_state.is_file() || !rollback_manifest.is_file() {
        return Err("boot-state and rollback-manifest evidence files are required".to_string());
    }

    let output_root = receipt_directory()?.join(format!(
        "rollback-bundle-{}",
        std::process::id()
    ));
    fs::create_dir_all(&output_root)
        .map_err(|error| format!("cannot create rollback bundle directory: {error}"))?;

    let directory = bridge_directory()?;
    let result = (|| {
        let script = directory.join("persist_windows_rollback_bundle.py");
        let boot_text = boot_state.to_string_lossy().to_string();
        let rollback_text = rollback_manifest.to_string_lossy().to_string();
        let output_text = output_root.to_string_lossy().to_string();
        let mut bundle = run_python_json(
            &script,
            &[
                "--boot-state",
                &boot_text,
                "--rollback-manifest",
                &rollback_text,
                "--output-dir",
                &output_text,
            ],
            &[],
        )?;
        if let Some(object) = bundle.as_object_mut() {
            object.insert(
                "bundle_directory".to_string(),
                Value::String(output_text),
            );
        }
        Ok(bundle)
    })();
    let _ = fs::remove_dir_all(&directory);
    result
}

fn google_drive_client_id() -> Option<String> {
    std::env::var(GOOGLE_DRIVE_CLIENT_ID_ENV)
        .ok()
        .or_else(|| option_env!("PHOENIX_KEY_GOOGLE_DRIVE_CLIENT_ID").map(str::to_string))
        .map(|value| value.trim().to_string())
        .filter(|value| value.ends_with(".apps.googleusercontent.com"))
}

#[tauri::command]
fn google_drive_picker_status() -> Value {
    let configured = !STORE_SAFE_DISTRIBUTION && google_drive_client_id().is_some();
    json!({
        "schema": "phoenix_key.google_drive_picker_status.v1",
        "configured": configured,
        "scope": GOOGLE_DRIVE_FILE_SCOPE,
        "selection_mode": "explicit_single_file",
        "system_browser_required": true,
        "oauth_token_persisted": false,
        "cloud_mutation_allowed": false
    })
}

fn validate_drive_operation_id(value: &str) -> Result<String, String> {
    let value = value.trim();
    if !(8..=64).contains(&value.len())
        || !value
            .bytes()
            .all(|byte| byte.is_ascii_alphanumeric() || byte == b'-' || byte == b'_')
    {
        return Err("Google Drive operation ID is malformed".to_string());
    }
    Ok(value.to_string())
}

fn drive_operation_paths(operation_id: &str) -> Result<(PathBuf, PathBuf), String> {
    let operation_id = validate_drive_operation_id(operation_id)?;
    let root = receipt_directory()?;
    Ok((
        root.join(format!("google-drive-{operation_id}.progress.json")),
        root.join(format!("google-drive-{operation_id}.cancel")),
    ))
}

#[tauri::command]
fn google_drive_acquisition_status(operation_id: String) -> Result<Value, String> {
    let (progress, cancel) = drive_operation_paths(&operation_id)?;
    if !progress.is_file() {
        return Ok(json!({
            "schema": "phoenix_key.google_drive_progress.v1",
            "phase": "waiting",
            "downloaded_size_bytes": 0,
            "provider_size_bytes": 0,
            "resume_offset_bytes": 0,
            "percent": 0.0,
            "cancel_requested": cancel.exists(),
            "read_only": true,
            "cloud_original_modified": false
        }));
    }
    let mut value: Value = serde_json::from_slice(
        &fs::read(&progress)
            .map_err(|error| format!("cannot read Drive progress receipt: {error}"))?,
    )
    .map_err(|error| format!("Drive progress receipt is invalid JSON: {error}"))?;
    if let Some(object) = value.as_object_mut() {
        object.insert(
            "cancel_requested".to_string(),
            Value::Bool(cancel.exists()),
        );
    }
    Ok(value)
}

#[tauri::command]
fn cancel_google_drive_acquisition(operation_id: String) -> Result<Value, String> {
    let (_, cancel) = drive_operation_paths(&operation_id)?;
    fs::write(&cancel, b"cancel")
        .map_err(|error| format!("cannot request Drive acquisition cancellation: {error}"))?;
    Ok(json!({
        "schema": "phoenix_key.google_drive_cancel.v1",
        "cancel_requested": true,
        "read_only": true,
        "cloud_original_modified": false
    }))
}

#[tauri::command]
async fn acquire_google_drive_picker_recovery(
    destination_dir: String,
    operation_id: String,
) -> Result<Value, String> {
    let destination = PathBuf::from(destination_dir.trim());
    if destination.as_os_str().is_empty() {
        return Err("Google Drive staging destination is required".to_string());
    }
    let client_id = google_drive_client_id().ok_or_else(|| {
        "Phoenix Key build is missing its Google Drive desktop OAuth client ID".to_string()
    })?;
    let (progress_file, cancel_file) = drive_operation_paths(&operation_id)?;
    let _ = fs::remove_file(&progress_file);
    let _ = fs::remove_file(&cancel_file);

    tauri::async_runtime::spawn_blocking(move || {
        let directory = bridge_directory()?;
        let result = (|| {
            let script = directory.join("google_drive_picker_recovery.py");
            let destination_text = destination.to_string_lossy().to_string();
            let progress_text = progress_file.to_string_lossy().to_string();
            let cancel_text = cancel_file.to_string_lossy().to_string();
            let mut receipt = run_python_json(
                &script,
                &[
                    "--destination-dir",
                    &destination_text,
                    "--progress-file",
                    &progress_text,
                    "--cancel-file",
                    &cancel_text,
                ],
                &[(GOOGLE_DRIVE_CLIENT_ID_ENV, client_id.as_str())],
            )?;
            if receipt.get("complete").and_then(Value::as_bool) != Some(true) {
                return Ok(receipt);
            }
            let staged_path = receipt
                .get("staged_path")
                .and_then(Value::as_str)
                .ok_or_else(|| {
                    "Google Picker receipt did not contain a staged path".to_string()
                })?;
            let identity = capture_source_identity(PathBuf::from(staged_path))?;
            if !identity.complete {
                return Err(
                    "Google Picker download source identity is incomplete".to_string(),
                );
            }
            let observed = receipt
                .get("observed_sha256")
                .and_then(Value::as_str)
                .ok_or_else(|| {
                    "Google Picker receipt did not contain a SHA-256".to_string()
                })?;
            if observed != identity.sha256 {
                return Err(
                    "Google Picker download changed before identity lock".to_string(),
                );
            }
            let object = receipt
                .as_object_mut()
                .ok_or_else(|| "Google Picker receipt is not a JSON object".to_string())?;
            object.insert(
                "source_identity".to_string(),
                serde_json::to_value(&identity)
                    .map_err(|error| format!("cannot serialize source identity: {error}"))?,
            );
            object.insert(
                "identity_lock_verified".to_string(),
                Value::Bool(true),
            );
            Ok(receipt)
        })();
        let _ = fs::remove_dir_all(&directory);
        let _ = fs::remove_file(&cancel_file);
        result
    })
    .await
    .map_err(|error| format!("Google Picker worker failed: {error}"))?
}

#[tauri::command]
fn plan_fat32_windows_media(source_root: String) -> Result<Value, String> {
    let source = PathBuf::from(source_root.trim());
    if !source.is_dir() {
        return Err(
            "FAT32 media planning requires an extracted Windows installation folder"
                .to_string(),
        );
    }

    let directory = bridge_directory()?;
    let result = (|| {
        let script = directory.join("plan_fat32_windows_media.py");
        let source_text = source.to_string_lossy().to_string();
        run_python_json(
            &script,
            &["--source-root", &source_text, "--split-size-mb", "3800"],
            &[],
        )
    })();
    let _ = fs::remove_dir_all(&directory);
    result
}

#[tauri::command]
fn stage_cloud_recovery_payload(
    source_file: String,
    destination: String,
    provider: String,
    provider_file_id: String,
    provider_name: String,
    provider_size_bytes: u64,
    provider_md5: Option<String>,
    expected_sha256: Option<String>,
) -> Result<Value, String> {
    let source = PathBuf::from(source_file.trim());
    if !source.is_file() {
        return Err("materialized cloud payload is not a regular file".to_string());
    }
    let destination = PathBuf::from(destination.trim());
    if destination.as_os_str().is_empty() {
        return Err("cloud staging destination is required".to_string());
    }
    if provider.trim().is_empty() || provider_file_id.trim().is_empty() {
        return Err("cloud provider and provider file ID are required".to_string());
    }
    if provider_size_bytes == 0 {
        return Err("cloud provider size must be positive".to_string());
    }

    let directory = bridge_directory()?;
    let result = (|| {
        let script = directory.join("stage_cloud_recovery_payload.py");
        let receipt = receipt_directory()?.join(format!(
            "phoenix-key-cloud-stage-{}-{}.json",
            std::process::id(),
            provider_file_id
                .chars()
                .filter(|ch| ch.is_ascii_alphanumeric())
                .take(12)
                .collect::<String>()
        ));
        let mut args = vec![
            "--source-file".to_string(),
            source.to_string_lossy().to_string(),
            "--destination".to_string(),
            destination.to_string_lossy().to_string(),
            "--receipt".to_string(),
            receipt.to_string_lossy().to_string(),
            "--provider".to_string(),
            provider.trim().to_string(),
            "--provider-file-id".to_string(),
            provider_file_id.trim().to_string(),
            "--provider-name".to_string(),
            provider_name,
            "--provider-size-bytes".to_string(),
            provider_size_bytes.to_string(),
        ];
        if let Some(md5) = provider_md5
            .as_deref()
            .map(str::trim)
            .filter(|value| !value.is_empty())
        {
            args.push("--provider-md5".to_string());
            args.push(md5.to_string());
        }
        if let Some(sha256) = expected_sha256
            .as_deref()
            .map(str::trim)
            .filter(|value| !value.is_empty())
        {
            args.push("--expected-sha256".to_string());
            args.push(sha256.to_string());
        }
        let refs: Vec<&str> = args.iter().map(String::as_str).collect();
        run_python_json(&script, &refs, &[])
    })();
    let _ = fs::remove_dir_all(&directory);
    result
}

#[tauri::command]
fn inspect_recovery_package_trust(
    package_path: String,
    expected_sha256: Option<String>,
    expected_signer_contains: Option<String>,
) -> Result<Value, String> {
    let package = PathBuf::from(package_path.trim());
    if !package.is_file() {
        return Err("recovery package does not exist or is not a regular file".to_string());
    }

    let directory = bridge_directory()?;
    let result = (|| {
        let script = directory.join("inspect_recovery_package_trust.py");
        let package_text = package.to_string_lossy().to_string();
        let mut args = vec!["--path".to_string(), package_text];
        if let Some(expected) = expected_sha256
            .as_deref()
            .map(str::trim)
            .filter(|value| !value.is_empty())
        {
            args.push("--expected-sha256".to_string());
            args.push(expected.to_string());
        }
        if let Some(signer) = expected_signer_contains
            .as_deref()
            .map(str::trim)
            .filter(|value| !value.is_empty())
        {
            args.push("--expected-signer-contains".to_string());
            args.push(signer.to_string());
        }
        let refs: Vec<&str> = args.iter().map(String::as_str).collect();
        run_python_json(&script, &refs, &[])
    })();
    let _ = fs::remove_dir_all(&directory);
    result
}

#[tauri::command]
fn inspect_windows_image_metadata(
    image_path: String,
    selected_index: Option<u32>,
    target_architecture: Option<String>,
) -> Result<Value, String> {
    let image = PathBuf::from(image_path.trim());
    if !image.is_file() {
        return Err("Windows image does not exist or is not a regular file".to_string());
    }

    let directory = bridge_directory()?;
    let result = (|| {
        let script = directory.join("inspect_windows_image_metadata.py");
        let image_text = image.to_string_lossy().to_string();
        let mut args = vec!["--path".to_string(), image_text];
        if let Some(index) = selected_index {
            if index == 0 {
                return Err("Windows image index must be greater than zero".to_string());
            }
            args.push("--index".to_string());
            args.push(index.to_string());
        }
        if let Some(architecture) = target_architecture
            .as_deref()
            .map(str::trim)
            .filter(|value| !value.is_empty())
        {
            args.push("--target-architecture".to_string());
            args.push(architecture.to_string());
        }
        let refs: Vec<&str> = args.iter().map(String::as_str).collect();
        run_python_json(&script, &refs, &[])
    })();
    let _ = fs::remove_dir_all(&directory);
    result
}

#[tauri::command]
fn inspect_bootcamp_driver_package(
    package_root: String,
    mac_model: String,
    expected_manifest_sha256: Option<String>,
) -> Result<Value, String> {
    let root = PathBuf::from(package_root.trim());
    if !root.is_dir() {
        return Err("Boot Camp support-software path is not a directory".to_string());
    }
    if mac_model.trim().is_empty() {
        return Err("exact Mac model identifier is required".to_string());
    }

    let directory = bridge_directory()?;
    let result = (|| {
        let script = directory.join("inspect_bootcamp_driver_package.py");
        let root_text = root.to_string_lossy().to_string();
        let mut args = vec![
            "--root".to_string(),
            root_text,
            "--mac-model".to_string(),
            mac_model.trim().to_string(),
        ];
        if let Some(expected) = expected_manifest_sha256
            .as_deref()
            .map(str::trim)
            .filter(|value| !value.is_empty())
        {
            args.push("--expected-manifest-sha256".to_string());
            args.push(expected.to_string());
        }
        let refs: Vec<&str> = args.iter().map(String::as_str).collect();
        run_python_json(&script, &refs, &[])
    })();
    let _ = fs::remove_dir_all(&directory);
    result
}

#[tauri::command]
fn verify_windows_recovery_target_identity(
    target_drive: String,
    expected_snapshot_identity_sha256: String,
    expected_stable_identity_sha256: String,
) -> Result<RecoveryTargetIdentityVerification, String> {
    if !cfg!(windows) {
        return Err("Windows target identity verification requires Windows.".to_string());
    }

    let resolution = resolve_target(target_drive.trim())?;
    if !resolution.is_windows_physical_drive() {
        return Err("recovery target must be an exact Windows PHYSICALDRIVE path".to_string());
    }

    let directory = bridge_directory()?;
    let result = (|| {
        let evidence = capture_write_evidence(
            &directory,
            &resolution.canonical_path,
            "phoenix-key-target-revalidation-evidence.json",
        )?;
        Ok(verify_recovery_target_identity(
            &evidence,
            &expected_snapshot_identity_sha256,
            &expected_stable_identity_sha256,
        ))
    })();
    let _ = fs::remove_dir_all(&directory);
    result
}

#[tauri::command]
fn locate_windows_recovery_target_by_stable_identity(
    expected_stable_identity_sha256: String,
) -> Result<Value, String> {
    if !cfg!(windows) {
        return Err("Stable target discovery requires Windows.".to_string());
    }

    let directory = bridge_directory()?;
    let result = (|| {
        let script = directory.join("find_windows_drive_by_stable_identity.py");
        run_python_json(
            &script,
            &[
                "--expected-stable-identity-sha256",
                expected_stable_identity_sha256.trim(),
            ],
            &[],
        )
    })();
    let _ = fs::remove_dir_all(&directory);
    result
}

#[tauri::command]
fn inspect_windows_recovery_target_reenumeration(
    current_target_drive: String,
    expected_target_drive: Option<String>,
    expected_snapshot_identity_sha256: String,
    expected_stable_identity_sha256: String,
) -> Result<Value, String> {
    if !cfg!(windows) {
        return Err("Windows target re-enumeration inspection requires Windows.".to_string());
    }

    let resolution = resolve_target(current_target_drive.trim())?;
    if !resolution.is_windows_physical_drive() {
        return Err("current recovery target must be an exact Windows PHYSICALDRIVE path".to_string());
    }

    let directory = bridge_directory()?;
    let result = (|| {
        let evidence = capture_write_evidence(
            &directory,
            &resolution.canonical_path,
            "phoenix-key-target-reenumeration-evidence.json",
        )?;
        let receipt = compare_recovery_target_reenumeration(
            &evidence,
            expected_target_drive.as_deref(),
            &expected_snapshot_identity_sha256,
            &expected_stable_identity_sha256,
        );

        let root = receipt_directory()?;
        let final_path = root.join(format!(
            "target-reenumeration-{}-{}.json",
            std::process::id(),
            &receipt.receipt_sha256[..12]
        ));
        let final_path_text = final_path.to_string_lossy().to_string();

        let mut value = serde_json::to_value(&receipt)
            .map_err(|error| format!("cannot serialize target re-enumeration receipt: {error}"))?;
        let object = value
            .as_object_mut()
            .ok_or_else(|| "target re-enumeration receipt is not a JSON object".to_string())?;
        object.insert(
            "receipt_path".to_string(),
            Value::String(final_path_text.clone()),
        );
        object.insert("receipt_persisted".to_string(), Value::Bool(true));

        let mut bytes = serde_json::to_vec_pretty(&value)
            .map_err(|error| format!("cannot encode target re-enumeration receipt: {error}"))?;
        bytes.push(b'\n');

        if final_path.exists() {
            let existing = fs::read(&final_path)
                .map_err(|error| format!("cannot read existing re-enumeration receipt: {error}"))?;
            if existing != bytes {
                return Err("target re-enumeration receipt path collision".to_string());
            }
            return Ok(value);
        }

        let temporary_path = final_path.with_extension("json.tmp");
        fs::write(&temporary_path, &bytes)
            .map_err(|error| format!("cannot persist target re-enumeration receipt: {error}"))?;
        fs::rename(&temporary_path, &final_path)
            .map_err(|error| format!("cannot finalize target re-enumeration receipt: {error}"))?;
        Ok(value)
    })();
    let _ = fs::remove_dir_all(&directory);
    result
}

#[tauri::command]
fn capture_restore_target_rollback_artifacts(
    target_drive: String,
    rollback_destination_path: String,
    rollback_contract_json: String,
) -> Result<Value, String> {
    if !cfg!(windows) {
        return Err("Restore rollback artifact capture requires Windows.".to_string());
    }

    let rollback_contract: Value = serde_json::from_str(&rollback_contract_json)
        .map_err(|error| format!("invalid rollback contract JSON: {error}"))?;
    if !verify_restore_target_rollback_contract_sha256(&rollback_contract) {
        return Err("rollback contract checksum is invalid".to_string());
    }
    if rollback_contract.get("schema").and_then(Value::as_str)
        != Some("phoenix_key.restore_target_rollback_contract.v1")
        || rollback_contract
            .get("restore_unlock_ready")
            .and_then(Value::as_bool)
            != Some(false)
        || rollback_contract
            .get("system_mutations_performed")
            .and_then(Value::as_bool)
            != Some(false)
    {
        return Err("rollback contract is not in the required locked planning state".to_string());
    }
    let contract_sha256 = rollback_contract
        .get("contract_sha256")
        .and_then(Value::as_str)
        .ok_or_else(|| "rollback contract SHA-256 is missing".to_string())?;
    let expected_snapshot = rollback_contract
        .get("target_identity_sha256")
        .and_then(Value::as_str)
        .ok_or_else(|| "rollback contract target snapshot identity is missing".to_string())?;
    let expected_stable = rollback_contract
        .get("target_stable_identity_sha256")
        .and_then(Value::as_str)
        .ok_or_else(|| "rollback contract target stable identity is missing".to_string())?;

    let valid_sha256 = |value: &str| {
        value.len() == 64 && value.bytes().all(|byte| byte.is_ascii_hexdigit())
    };
    if !valid_sha256(contract_sha256)
        || !valid_sha256(expected_snapshot)
        || !valid_sha256(expected_stable)
    {
        return Err("rollback contract contains an invalid SHA-256 identity".to_string());
    }
    let apply_system_image_blocked = rollback_contract
        .get("always_blocked_by_this_contract")
        .and_then(Value::as_array)
        .is_some_and(|items| {
            items
                .iter()
                .filter_map(Value::as_str)
                .any(|item| item == "apply_system_image")
        });
    if !apply_system_image_blocked
        || rollback_contract
            .get("artifact_destination_requirement")
            .and_then(Value::as_str)
            != Some("separate-physical-device-from-restore-target")
        || rollback_contract
            .get("fresh_target_revalidation_required")
            .and_then(Value::as_bool)
            != Some(true)
    {
        return Err("rollback contract is missing mandatory restore safety locks".to_string());
    }

    let target_resolution = resolve_target(target_drive.trim())?;
    if !target_resolution.is_windows_physical_drive() {
        return Err("restore target must be an exact Windows PHYSICALDRIVE path".to_string());
    }

    let destination_root = PathBuf::from(rollback_destination_path.trim());
    if !destination_root.is_dir() {
        return Err("rollback destination must be an existing directory".to_string());
    }

    let directory = bridge_directory()?;
    let result = (|| {
        let target_evidence_name = "phoenix-key-restore-rollback-target-evidence.json";
        let target_evidence = capture_write_evidence(
            &directory,
            &target_resolution.canonical_path,
            target_evidence_name,
        )?;
        let target_evidence_path = directory.join(target_evidence_name);

        let resolver = directory.join("resolve_windows_source_disk.py");
        let destination_text = destination_root.to_string_lossy().to_string();
        let destination_resolution = run_python_json(
            &resolver,
            &["--source", &destination_text],
            &[],
        )?;
        let destination_verification = assess_rollback_destination(
            &target_evidence,
            &destination_resolution,
            &destination_text,
            expected_stable,
        );
        if !destination_verification.ready_for_hardware_rollback_capture {
            return Err(format!(
                "rollback destination is not safely separated from the restore target: {:?}",
                destination_verification.block_reasons
            ));
        }

        let destination_stable = destination_verification
            .destination_stable_identity_sha256
            .as_deref()
            .ok_or_else(|| "rollback destination stable identity is missing".to_string())?;
        let logical_sector_size = target_evidence
            .pointer("/disk/logical_sector_size")
            .and_then(Value::as_u64)
            .ok_or_else(|| "target logical sector size is missing from drive evidence".to_string())?;
        if !(512..=4096).contains(&logical_sector_size) {
            return Err("target logical sector size is outside the supported 512-4096 range".to_string());
        }

        let output_root = destination_root.join(format!(
            "phoenix-key-restore-rollback-{}-{}",
            std::process::id(),
            &expected_snapshot[..12]
        ));
        if output_root.exists() {
            return Err("dedicated rollback capture directory already exists".to_string());
        }

        let script = directory.join("capture_windows_restore_rollback.py");
        let evidence_text = target_evidence_path.to_string_lossy().to_string();
        let output_text = output_root.to_string_lossy().to_string();
        let sector_text = logical_sector_size.to_string();
        run_python_json(
            &script,
            &[
                "--target",
                &target_resolution.canonical_path,
                "--drive-evidence",
                &evidence_text,
                "--output-dir",
                &output_text,
                "--logical-sector-size",
                &sector_text,
                "--expected-target-snapshot-identity-sha256",
                expected_snapshot,
                "--expected-target-stable-identity-sha256",
                expected_stable,
                "--expected-destination-stable-identity-sha256",
                destination_stable,
                "--destination-stable-identity-sha256",
                destination_stable,
                "--rollback-contract-sha256",
                contract_sha256,
            ],
            &[],
        )
    })();
    let _ = fs::remove_dir_all(&directory);
    result
}

#[tauri::command]
fn capture_restore_target_boot_metadata(
    rollback_capture_receipt_json: String,
    rollback_contract_json: String,
) -> Result<Value, String> {
    if !cfg!(windows) {
        return Err("Restore target boot-metadata capture requires Windows.".to_string());
    }

    let rollback_capture: Value = serde_json::from_str(&rollback_capture_receipt_json)
        .map_err(|error| format!("invalid rollback capture receipt JSON: {error}"))?;
    let rollback_contract: Value = serde_json::from_str(&rollback_contract_json)
        .map_err(|error| format!("invalid rollback contract JSON: {error}"))?;

    if !verify_restore_target_rollback_contract_sha256(&rollback_contract) {
        return Err("rollback contract checksum is invalid".to_string());
    }
    if rollback_capture.get("schema").and_then(Value::as_str)
        != Some("phoenix_key.restore_target_rollback_capture.v1")
        || rollback_capture
            .get("target_bytes_written")
            .and_then(Value::as_u64)
            != Some(0)
        || rollback_capture
            .get("target_write_attempted")
            .and_then(Value::as_bool)
            != Some(false)
        || rollback_capture
            .get("restore_unlock_ready")
            .and_then(Value::as_bool)
            != Some(false)
    {
        return Err("rollback capture receipt does not preserve required safety locks".to_string());
    }

    let target = rollback_capture
        .get("target")
        .and_then(Value::as_str)
        .ok_or_else(|| "rollback capture target is missing".to_string())?;
    let expected_snapshot = rollback_capture
        .get("target_snapshot_identity_sha256")
        .and_then(Value::as_str)
        .ok_or_else(|| "rollback capture target snapshot identity is missing".to_string())?;
    let expected_stable = rollback_capture
        .get("target_stable_identity_sha256")
        .and_then(Value::as_str)
        .ok_or_else(|| "rollback capture target stable identity is missing".to_string())?;
    let capture_contract_sha = rollback_capture
        .get("rollback_contract_sha256")
        .and_then(Value::as_str)
        .ok_or_else(|| "rollback capture contract SHA-256 is missing".to_string())?;
    let contract_sha = rollback_contract
        .get("contract_sha256")
        .and_then(Value::as_str)
        .ok_or_else(|| "rollback contract SHA-256 is missing".to_string())?;
    let contract_snapshot = rollback_contract
        .get("target_identity_sha256")
        .and_then(Value::as_str)
        .ok_or_else(|| "rollback contract target snapshot identity is missing".to_string())?;
    let contract_stable = rollback_contract
        .get("target_stable_identity_sha256")
        .and_then(Value::as_str)
        .ok_or_else(|| "rollback contract target stable identity is missing".to_string())?;

    let valid_sha256 = |value: &str| {
        value.len() == 64 && value.bytes().all(|byte| byte.is_ascii_hexdigit())
    };
    if !valid_sha256(expected_snapshot)
        || !valid_sha256(expected_stable)
        || !valid_sha256(capture_contract_sha)
        || !valid_sha256(contract_sha)
        || !valid_sha256(contract_snapshot)
        || !valid_sha256(contract_stable)
        || !capture_contract_sha.eq_ignore_ascii_case(contract_sha)
        || !expected_snapshot.eq_ignore_ascii_case(contract_snapshot)
        || !expected_stable.eq_ignore_ascii_case(contract_stable)
    {
        return Err("rollback capture and rollback contract identities do not match".to_string());
    }

    let target_resolution = resolve_target(target)?;
    if !target_resolution.is_windows_physical_drive() {
        return Err("restore target must remain an exact Windows PHYSICALDRIVE path".to_string());
    }

    let rollback_output = rollback_capture
        .get("output_directory")
        .and_then(Value::as_str)
        .ok_or_else(|| "rollback capture output directory is missing".to_string())?;
    let rollback_output = PathBuf::from(rollback_output);
    if !rollback_output.is_dir() {
        return Err("rollback capture output directory is not available".to_string());
    }
    let output_dir = rollback_output.join("boot-metadata");
    if output_dir.exists() {
        return Err("boot-metadata output directory already exists".to_string());
    }

    let directory = bridge_directory()?;
    let result = (|| {
        let evidence_name = "phoenix-key-boot-metadata-target-evidence.json";
        let evidence = capture_write_evidence(
            &directory,
            &target_resolution.canonical_path,
            evidence_name,
        )?;
        let observed_snapshot = evidence
            .pointer("/disk/identity_sha256")
            .and_then(Value::as_str)
            .ok_or_else(|| "fresh target snapshot identity is missing".to_string())?;
        let observed_stable = evidence
            .pointer("/disk/stable_identity_sha256")
            .and_then(Value::as_str)
            .ok_or_else(|| "fresh target stable identity is missing".to_string())?;
        if !observed_snapshot.eq_ignore_ascii_case(expected_snapshot)
            || !observed_stable.eq_ignore_ascii_case(expected_stable)
        {
            return Err(
                "restore target identity changed after GPT rollback capture; reanalysis required"
                    .to_string(),
            );
        }

        let rollback_receipt_path = directory.join("restore-rollback-capture.json");
        let mut rollback_bytes = serde_json::to_vec_pretty(&rollback_capture)
            .map_err(|error| format!("cannot encode rollback capture receipt: {error}"))?;
        rollback_bytes.push(b'\n');
        fs::write(&rollback_receipt_path, rollback_bytes)
            .map_err(|error| format!("cannot stage rollback capture receipt: {error}"))?;

        let script = directory.join("capture_windows_restore_target_boot_metadata.py");
        let evidence_path = directory.join(evidence_name);
        let evidence_text = evidence_path.to_string_lossy().to_string();
        let rollback_text = rollback_receipt_path.to_string_lossy().to_string();
        let output_text = output_dir.to_string_lossy().to_string();
        run_python_json(
            &script,
            &[
                "--target",
                &target_resolution.canonical_path,
                "--drive-evidence",
                &evidence_text,
                "--rollback-capture-receipt",
                &rollback_text,
                "--rollback-contract-sha256",
                contract_sha,
                "--output-dir",
                &output_text,
            ],
            &[],
        )
    })();
    let _ = fs::remove_dir_all(&directory);
    result
}

#[tauri::command]
fn inspect_restore_rollback_destination(
    target_drive: String,
    rollback_destination_path: String,
    expected_target_stable_identity_sha256: String,
) -> Result<RollbackDestinationVerification, String> {
    if !cfg!(windows) {
        return Err("Rollback destination verification requires Windows.".to_string());
    }

    let target_resolution = resolve_target(target_drive.trim())?;
    if !target_resolution.is_windows_physical_drive() {
        return Err("restore target must be an exact Windows PHYSICALDRIVE path".to_string());
    }

    let destination = PathBuf::from(rollback_destination_path.trim());
    if !destination.is_dir() {
        return Err("rollback destination must be an existing directory".to_string());
    }

    let directory = bridge_directory()?;
    let result = (|| {
        let target_evidence = capture_write_evidence(
            &directory,
            &target_resolution.canonical_path,
            "phoenix-key-rollback-destination-target-evidence.json",
        )?;

        let resolver = directory.join("resolve_windows_source_disk.py");
        let destination_text = destination.to_string_lossy().to_string();
        let destination_resolution = run_python_json(
            &resolver,
            &["--source", &destination_text],
            &[],
        )?;

        Ok(assess_rollback_destination(
            &target_evidence,
            &destination_resolution,
            &destination_text,
            &expected_target_stable_identity_sha256,
        ))
    })();
    let _ = fs::remove_dir_all(&directory);
    result
}

#[tauri::command]
fn inspect_recovery_target_safety(
    target_drive: String,
    source_path: String,
) -> Result<RecoveryTargetSafety, String> {
    if !cfg!(windows) {
        return Err("Windows physical-target safety inspection requires Windows.".to_string());
    }

    let resolution = resolve_target(target_drive.trim())?;
    if !resolution.is_windows_physical_drive() {
        return Err("recovery target must be an exact Windows PHYSICALDRIVE path".to_string());
    }

    let source = PathBuf::from(source_path.trim());
    let source_identity = capture_source_identity(&source)?;
    if !source_identity.complete || source_identity.size_bytes == 0 {
        return Err("recovery source identity is incomplete or empty".to_string());
    }

    let directory = bridge_directory()?;
    let result = (|| {
        let evidence = capture_write_evidence(
            &directory,
            &resolution.canonical_path,
            "phoenix-key-recovery-target-evidence.json",
        )?;

        let resolver = directory.join("resolve_windows_source_disk.py");
        let source_text = source.to_string_lossy().to_string();
        let source_disk = run_python_json(
            &resolver,
            &["--source", &source_text],
            &[],
        )?;
        let source_physical_target = source_disk
            .pointer("/source/physical_target")
            .and_then(Value::as_str)
            .ok_or_else(|| "source physical-device proof is missing".to_string())?;
        let source_stable_identity = source_disk
            .pointer("/source/stable_identity_sha256")
            .and_then(Value::as_str)
            .ok_or_else(|| "source stable physical-device identity is missing".to_string())?;

        Ok(assess_recovery_target(
            &evidence,
            source_identity.size_bytes,
            Some(source_physical_target),
            Some(source_stable_identity),
        ))
    })();
    let _ = fs::remove_dir_all(&directory);
    result
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
        let source_identity = capture_source_identity(&image)?;
        if !source_identity.complete {
            return Err("source image identity is incomplete".to_string());
        }
        Ok(json!({
            "schema": "phoenix_key.write_preparation.v1",
            "target": target,
            "target_identity_sha256": identity,
            "target_size_bytes": size,
            "image_path": image.to_string_lossy(),
            "image_size_bytes": image_size,
            "image_sha256": source_identity.sha256.clone(),
            "authorization_phrase": expected_authorization(
                target,
                identity,
                size,
                &source_identity.sha256,
            ),
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
        let source_identity = capture_source_identity(&image)?;
        if !source_identity.complete {
            return Err("source image identity is incomplete".to_string());
        }
        let required = expected_authorization(
            target,
            identity,
            size,
            &source_identity.sha256,
        );
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

    let builder = tauri::Builder::default();

    #[cfg(feature = "store-safe")]
    let builder = builder.invoke_handler(tauri::generate_handler![
        distribution_profile,
        analyze_windows_recovery_source,
        plan_windows_recovery_source,
        verify_windows_recovery_source_identity
    ]);

    #[cfg(not(feature = "store-safe"))]
    let builder = builder.invoke_handler(tauri::generate_handler![
        distribution_profile,
        scan_connected_devices,
        scan_media_targets,
        plan_media_build,
        prepare_media_write,
        execute_media_write,
        analyze_windows_recovery_source,
        plan_windows_recovery_source,
        verify_windows_recovery_source_identity,
        build_windows_recovery_evidence_bundle_v2,
        plan_windows_boot_repair,
        create_target_data_preservation_decision,
        inspect_mac_bootcamp_host,
        inspect_recovery_package_trust,
        inspect_windows_image_metadata,
        assess_windows_restore_readiness,
        assess_windows_restore_hardware_preflight,
        plan_restore_target_rollback_contract,
        inspect_bootcamp_driver_package,
        inspect_recovery_target_safety,
        inspect_restore_rollback_destination,
        capture_restore_target_rollback_artifacts,
        capture_restore_target_boot_metadata,
        verify_windows_recovery_target_identity,
        locate_windows_recovery_target_by_stable_identity,
        inspect_windows_recovery_target_reenumeration,
        assess_intel_mac_restore_readiness,
        google_drive_picker_status,
        google_drive_acquisition_status,
        cancel_google_drive_acquisition,
        acquire_google_drive_picker_recovery,
        plan_fat32_windows_media,
        stage_cloud_recovery_payload,
        capture_windows_recovery_baseline,
        persist_windows_recovery_rollback_bundle
    ]);

    builder
        .run(tauri::generate_context!())
        .expect("failed to run Phoenix Key desktop application");
}

#[cfg(test)]
mod tests {
    use super::{
        attach_target_resolution, current_distribution_profile, expected_authorization,
        installed_smoke_receipt, require_write_candidate, resolve_target,
        validate_drive_operation_id,
    };
    use serde_json::json;

    #[cfg(feature = "store-safe")]
    #[test]
    fn store_safe_build_cannot_stage_external_helpers() {
        let error = super::bridge_directory().unwrap_err();
        assert_eq!(
            error,
            "external helper execution is disabled in the store-safe distribution"
        );
    }

    #[test]
    fn distribution_profile_matches_compile_time_channel() {
        let profile = current_distribution_profile();
        assert_eq!(profile.schema, "phoenix_key.distribution_profile.v1");
        assert_eq!(profile.store_safe, cfg!(feature = "store-safe"));
        assert_eq!(profile.native_recovery_analysis, true);
        assert_eq!(profile.physical_media_write, !cfg!(feature = "store-safe"));
        assert_eq!(profile.external_helper_execution, !cfg!(feature = "store-safe"));
    }

    #[test]
    fn drive_operation_id_blocks_path_traversal() {
        assert!(validate_drive_operation_id("drive-123456").is_ok());
        assert!(validate_drive_operation_id("../../escape").is_err());
        assert!(validate_drive_operation_id("short").is_err());
    }

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
    fn authorization_binds_target_and_source_identity() {
        assert_eq!(
            expected_authorization(
                r"\\.\physicaldrive7",
                "abc123",
                4096,
                &"d".repeat(64),
            ),
            format!(
                r"I AUTHORIZE COMPLETE DESTRUCTION OF \\.\PHYSICALDRIVE7 IDENTITY abc123 SIZE 4096 SOURCE_SHA256 {}",
                "d".repeat(64)
            )
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
