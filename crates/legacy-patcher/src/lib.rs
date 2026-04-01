use anyhow::{anyhow, Context, Result};
use phoenix_content::prepare_source;
use phoenix_core::DeviceGraph;
use phoenix_report::{create_report_bundle_with_meta_and_signing, ReportPaths};
use phoenix_safety::{can_write_to_disk, SafetyContext, SafetyDecision};
use plist::Value;
use std::fs;
use std::path::{Path, PathBuf};

#[derive(Debug, Clone)]
pub struct LegacyPatchParams {
    pub source_path: PathBuf,
    pub report_base: PathBuf,
    pub model: Option<String>,
    pub board_id: Option<String>,
    pub force: bool,
    pub confirmation_token: Option<String>,
    pub dry_run: bool,
}

#[derive(Debug, Clone)]
pub struct LegacyPatchResult {
    pub report: ReportPaths,
    pub patched_files: Vec<String>,
    pub dry_run: bool,
}

pub fn run_legacy_patch(params: &LegacyPatchParams) -> Result<LegacyPatchResult> {
    let graph = build_device_graph()?;
    let ctx = SafetyContext {
        force_mode: params.force,
        confirmation_token: params.confirmation_token.clone(),
    };
    match can_write_to_disk(&ctx, false) {
        SafetyDecision::Allow => {}
        SafetyDecision::Deny(reason) => return Err(anyhow!(reason)),
    }

    let prepared = prepare_source(&params.source_path)?;
    let source_root = prepared.root.clone();
    let app_root = find_install_app(&source_root)
        .ok_or_else(|| anyhow!("install macOS.app not found in source"))?;
    let candidates = patch_candidates(&app_root);

    let model = params.model.clone().unwrap_or_else(|| "UnknownModel".to_string());
    let board_id = params.board_id.clone();

    let mut patched = Vec::new();
    let mut logs = Vec::new();
    logs.push("workflow=macos-legacy-patch".to_string());
    logs.push(format!("source_app={}", app_root.display()));
    logs.push(format!("model={}", model));
    if let Some(board_id) = &board_id {
        logs.push(format!("board_id={}", board_id));
    }

    for path in candidates {
        if !path.exists() {
            continue;
        }
        let mut value = Value::from_file(&path)
            .with_context(|| format!("read {}", path.display()))?;
        let mut changed = false;
        changed |= patch_supported_models(&mut value, &model);
        if let Some(board) = &board_id {
            changed |= patch_supported_board_ids(&mut value, board);
        }
        if changed {
            if !params.dry_run {
                value
                    .to_file_xml(&path)
                    .with_context(|| format!("write {}", path.display()))?;
            }
            patched.push(path.display().to_string());
        }
    }

    if patched.is_empty() {
        logs.push("patches_applied=0".to_string());
    } else {
        logs.push(format!("patches_applied={}", patched.len()));
    }

    let meta = serde_json::json!({
        "workflow": "macos-legacy-patch",
        "status": if params.dry_run { "dry_run" } else { "completed" },
        "patched_files": patched,
        "model": model,
        "board_id": board_id,
    });

    let report = create_report_bundle_with_meta_and_signing(
        &params.report_base,
        &graph,
        Some(meta),
        Some(&logs.join("\n")),
        signing_key_from_env().as_deref(),
    )?;

    Ok(LegacyPatchResult {
        report,
        patched_files: patched,
        dry_run: params.dry_run,
    })
}

fn patch_candidates(app_root: &Path) -> Vec<PathBuf> {
    vec![
        app_root.join("Contents/SharedSupport/PlatformSupport.plist"),
        app_root.join("Contents/SharedSupport/InstallInfo.plist"),
        app_root.join("Contents/Resources/InstallInfo.plist"),
    ]
}

fn patch_supported_models(value: &mut Value, model: &str) -> bool {
    let keys = [
        "SupportedModels",
        "SupportedModelProperties",
        "SupportedDeviceModels",
    ];
    update_plist_arrays(value, &keys, model)
}

fn patch_supported_board_ids(value: &mut Value, board_id: &str) -> bool {
    let keys = ["BoardIDs", "SupportedBoardIDs", "SupportedBoardIds"];
    update_plist_arrays(value, &keys, board_id)
}

fn update_plist_arrays(value: &mut Value, keys: &[&str], entry: &str) -> bool {
    let mut changed = false;
    for key in keys {
        if let Some(array) = find_array_mut(value, key) {
            if !array.iter().any(|item| item.as_string() == Some(entry)) {
                array.push(Value::String(entry.to_string()));
                changed = true;
            }
        }
    }
    changed
}

fn find_array_mut<'a>(value: &'a mut Value, key: &str) -> Option<&'a mut Vec<Value>> {
    let dict = value.as_dictionary_mut()?;
    let entry = dict.entry(key.to_string()).or_insert_with(|| Value::Array(Vec::new()));
    entry.as_array_mut()
}

fn find_install_app(root: &Path) -> Option<PathBuf> {
    if root.extension().and_then(|e| e.to_str()).map(|e| e.eq_ignore_ascii_case("app")).unwrap_or(false)
        && root.join("Contents/Resources/createinstallmedia").exists()
    {
        return Some(root.to_path_buf());
    }
    let entries = fs::read_dir(root).ok()?;
    for entry in entries.flatten() {
        let path = entry.path();
        if path
            .extension()
            .and_then(|e| e.to_str())
            .map(|e| e.eq_ignore_ascii_case("app"))
            .unwrap_or(false)
            && path.join("Contents/Resources/createinstallmedia").exists()
        {
            return Some(path);
        }
    }
    None
}

fn signing_key_from_env() -> Option<String> {
    std::env::var("PHOENIX_SIGNING_KEY").ok()
}

fn build_device_graph() -> Result<DeviceGraph> {
    #[cfg(target_os = "windows")]
    {
        return phoenix_host_windows::build_device_graph();
    }
    #[cfg(target_os = "linux")]
    {
        return phoenix_host_linux::build_device_graph();
    }
    #[cfg(target_os = "macos")]
    {
        return phoenix_host_macos::build_device_graph();
    }
    #[cfg(not(any(target_os = "windows", target_os = "linux", target_os = "macos")))]
    {
        Err(anyhow!("unsupported OS"))
    }
}
